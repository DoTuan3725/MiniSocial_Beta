from django.db import models

from common.models import BaseModel


class PostMedia(BaseModel):
    """
    Bảng 6 - post_media: tệp ảnh/video đính kèm bài viết, thuộc phân hệ Media.
    Liên kết tới posts bằng khóa ngoại dạng chuỗi 'posts.Post' (không import model chéo).
    status: PROCESSING (Celery đang nén) -> READY | FAILED.
    """

    class MediaType(models.TextChoices):
        IMAGE = "IMAGE", "Hình ảnh"
        VIDEO = "VIDEO", "Video"

    class Status(models.TextChoices):
        PROCESSING = "PROCESSING", "Đang xử lý"
        READY = "READY", "Sẵn sàng"
        FAILED = "FAILED", "Lỗi xử lý"

    post = models.ForeignKey("posts.Post", on_delete=models.CASCADE, related_name="media_files")
    media_type = models.CharField(max_length=10, choices=MediaType.choices, default=MediaType.IMAGE)
    file_url = models.CharField(max_length=500, blank=True, default="")
    thumbnail_url = models.CharField(max_length=500, blank=True, default="")
    mime_type = models.CharField(max_length=50, blank=True, default="")
    file_size = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PROCESSING)
    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "post_media"
        ordering = ["display_order"]
        verbose_name = "Tệp đính kèm"
        verbose_name_plural = "Tệp đính kèm"
