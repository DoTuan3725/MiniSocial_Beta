"""
MEDIA SERVICE - giao diện công khai của phân hệ Media.
Luồng (Kịch bản 3): Backend nhận file -> kiểm tra MIME thật + dung lượng <= 10MB -> lưu tệp tạm
-> đẩy task Celery -> Worker nén WebP + thumbnail -> đẩy lên R2/MinIO -> cập nhật URL.
"""

import logging
from pathlib import Path

import uuid6
from django.conf import settings
from django.db import transaction
from PIL import Image

from common.exceptions import ServiceError

from .models import PostMedia
from .storage import public_url

logger = logging.getLogger(__name__)

IMAGE_MIMES = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp", "image/gif": "gif"}
VIDEO_MIMES = {"video/mp4": "mp4", "video/webm": "webm", "video/quicktime": "mov"}
PURPOSES = {"avatar", "cover", "chat"}


def sniff_mime(head):
    """Nhận diện định dạng bằng chữ ký byte thật (magic number), không tin phần mở rộng tên tệp."""
    if head.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if head[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "image/webp"
    if head[4:8] == b"ftyp":
        return "video/quicktime" if head[8:12] == b"qt  " else "video/mp4"
    if head.startswith(b"\x1a\x45\xdf\xa3"):
        return "video/webm"
    return None


def validate_upload(uploaded):
    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    if uploaded.size > max_bytes:
        raise ServiceError(f"Tệp '{uploaded.name}' vượt quá {settings.MAX_UPLOAD_MB}MB", code="FILE_TOO_LARGE")
    uploaded.seek(0)
    head = uploaded.read(32)
    uploaded.seek(0)
    mime = sniff_mime(head)
    if mime not in IMAGE_MIMES and mime not in VIDEO_MIMES:
        raise ServiceError(
            f"Tệp '{uploaded.name}' không đúng định dạng. Chỉ nhận ảnh JPG/PNG/WebP/GIF hoặc video MP4/WebM/MOV.",
            code="FILE_TYPE_NOT_ALLOWED",
        )
    if mime in IMAGE_MIMES:
        try:
            with Image.open(uploaded) as img:
                img.verify()
        except Exception:  # noqa: BLE001
            raise ServiceError(f"Ảnh '{uploaded.name}' bị hỏng hoặc không đọc được", code="FILE_CORRUPTED")
        finally:
            uploaded.seek(0)
    kind = PostMedia.MediaType.IMAGE if mime in IMAGE_MIMES else PostMedia.MediaType.VIDEO
    return kind, mime


def _save_temp(uploaded, mime):
    ext = IMAGE_MIMES.get(mime) or VIDEO_MIMES.get(mime)
    temp_dir = Path(settings.TEMP_UPLOAD_DIR)
    temp_dir.mkdir(parents=True, exist_ok=True)
    path = temp_dir / f"{uuid6.uuid7()}.{ext}"
    with open(path, "wb") as fh:
        for chunk in uploaded.chunks():
            fh.write(chunk)
    return str(path)


def _target_keys(prefix, base_name, mime):
    if mime in IMAGE_MIMES and mime != "image/gif":
        return f"{prefix}/{base_name}.webp", f"{prefix}/{base_name}_thumb.webp", "image/webp"
    ext = IMAGE_MIMES.get(mime) or VIDEO_MIMES.get(mime)
    return f"{prefix}/{base_name}.{ext}", "", mime


def validate_many(files):
    if len(files) > settings.MAX_FILES_PER_POST:
        raise ServiceError(f"Mỗi bài viết tối đa {settings.MAX_FILES_PER_POST} tệp")
    return [validate_upload(f) for f in files]


def attach_post_media(post_id, files, validated=None):
    """Tạo bản ghi post_media (PROCESSING) và đẩy task nén cho từng tệp."""
    from .tasks import process_upload

    validated = validated or validate_many(files)
    created = []
    for order, (uploaded, (kind, mime)) in enumerate(zip(files, validated)):
        media = PostMedia.objects.create(
            post_id=post_id, media_type=kind, mime_type=mime, file_size=uploaded.size, display_order=order
        )
        temp_path = _save_temp(uploaded, mime)
        key, thumb_key, _ = _target_keys("posts", str(media.id), mime)
        media.file_url = public_url(key)
        media.thumbnail_url = public_url(thumb_key) if thumb_key else ""
        media.save(update_fields=["file_url", "thumbnail_url"])
        transaction.on_commit(
            lambda p=temp_path, k=key, t=thumb_key, m=mime, mid=str(media.id): process_upload.delay(p, k, t, m, mid)
        )
        created.append(media)
    return created


def upload_single(uploaded, purpose):
    """Ảnh đại diện / ảnh bìa / ảnh trong chat. Trả URL đích ngay, Celery xử lý nền."""
    from .tasks import process_upload

    if purpose not in PURPOSES:
        raise ServiceError("purpose phải là avatar | cover | chat")
    kind, mime = validate_upload(uploaded)
    if purpose in ("avatar", "cover") and kind != PostMedia.MediaType.IMAGE:
        raise ServiceError("Ảnh đại diện / ảnh bìa phải là tệp hình ảnh")
    temp_path = _save_temp(uploaded, mime)
    key, thumb_key, out_mime = _target_keys(purpose + "s", str(uuid6.uuid7()), mime)
    transaction.on_commit(lambda: process_upload.delay(temp_path, key, thumb_key, mime, None))
    return {
        "url": public_url(key),
        "thumbnail_url": public_url(thumb_key) if thumb_key else "",
        "media_type": kind,
        "mime_type": out_mime,
        "status": "PROCESSING",
    }


def serialize_media(media):
    return {
        "id": str(media.id),
        "media_type": media.media_type,
        "file_url": media.file_url,
        "thumbnail_url": media.thumbnail_url,
        "status": media.status,
        "display_order": media.display_order,
    }


def media_for_posts(post_ids):
    result = {str(pid): [] for pid in post_ids}
    for m in PostMedia.objects.filter(post_id__in=list(result.keys())).order_by("display_order"):
        result[str(m.post_id)].append(serialize_media(m))
    return result


def storage_stats():
    from django.db.models import Count, Sum

    agg = PostMedia.objects.aggregate(total=Count("id"), bytes=Sum("file_size"))
    return {"media_files": agg["total"] or 0, "media_bytes_uploaded": agg["bytes"] or 0}
