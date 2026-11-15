import logging
import os
import time
from pathlib import Path

from celery import shared_task
from django.conf import settings

from . import processing
from .models import PostMedia
from .storage import get_storage

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=5)
def process_upload(self, temp_path, key, thumb_key, mime, media_id=None):
    """
    Celery Worker: nén ảnh sang WebP (giảm ~80% dung lượng), cắt thumbnail 150x150,
    stream lên Cloudflare R2 / MinIO, cập nhật trạng thái post_media.
    GIF động và video được giữ nguyên định dạng.
    """
    storage = get_storage()
    try:
        with open(temp_path, "rb") as fh:
            data = fh.read()
        if mime.startswith("image/") and mime != "image/gif":
            storage.put(key, processing.to_webp(data), "image/webp")
            if thumb_key:
                storage.put(thumb_key, processing.make_thumbnail(data), "image/webp")
        else:
            storage.put(key, data, mime)
        if media_id:
            PostMedia.objects.filter(id=media_id).update(status=PostMedia.Status.READY)
    except FileNotFoundError:
        logger.error("Không tìm thấy tệp tạm %s", temp_path)
        if media_id:
            PostMedia.objects.filter(id=media_id).update(status=PostMedia.Status.FAILED)
        return False
    except Exception as exc:  # noqa: BLE001
        logger.exception("Xử lý media thất bại: %s", key)
        if self.request.retries >= self.max_retries:
            if media_id:
                PostMedia.objects.filter(id=media_id).update(status=PostMedia.Status.FAILED)
            _remove(temp_path)
            return False
        raise self.retry(exc=exc)
    _remove(temp_path)
    return True


def _remove(path):
    try:
        os.remove(path)
    except OSError:
        pass


@shared_task
def cleanup_temp_uploads(max_age_seconds=3600):
    """Quét dọn tệp tạm quá 1 giờ (ví dụ do worker dừng đột ngột)."""
    temp_dir = Path(settings.TEMP_UPLOAD_DIR)
    if not temp_dir.exists():
        return 0
    removed = 0
    now = time.time()
    for path in temp_dir.iterdir():
        if path.is_file() and now - path.stat().st_mtime > max_age_seconds:
            _remove(str(path))
            removed += 1
    return removed
