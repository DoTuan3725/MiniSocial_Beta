from django.conf import settings
from django.db import models

from common.models import BaseModel


class Notification(BaseModel):
    """
    Bảng 15 - notifications. Quan hệ đa hình (polymorphic): entity_type + entity_id
    trỏ tới POST | COMMENT | USER | GROUP | REPORT mà không cần khóa ngoại cứng tới từng bảng.
    """

    class Verb(models.TextChoices):
        FRIEND_REQUEST = "FRIEND_REQUEST", "Lời mời kết bạn"
        FRIEND_ACCEPTED = "FRIEND_ACCEPTED", "Chấp nhận kết bạn"
        POST_LIKED = "POST_LIKED", "Thích bài viết"
        POST_COMMENTED = "POST_COMMENTED", "Bình luận bài viết"
        COMMENT_REPLIED = "COMMENT_REPLIED", "Trả lời bình luận"
        POST_SHARED = "POST_SHARED", "Chia sẻ bài viết"
        GROUP_JOIN_REQUEST = "GROUP_JOIN_REQUEST", "Yêu cầu vào nhóm"
        GROUP_JOIN_APPROVED = "GROUP_JOIN_APPROVED", "Được duyệt vào nhóm"
        REPORT_RESOLVED = "REPORT_RESOLVED", "Báo cáo đã xử lý"
        SYSTEM = "SYSTEM", "Hệ thống"

    class EntityType(models.TextChoices):
        POST = "POST", "Bài viết"
        COMMENT = "COMMENT", "Bình luận"
        USER = "USER", "Người dùng"
        GROUP = "GROUP", "Nhóm"
        REPORT = "REPORT", "Báo cáo"

    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="triggered_notifications",
    )
    verb = models.CharField(max_length=30, choices=Verb.choices)
    entity_type = models.CharField(max_length=10, choices=EntityType.choices)
    entity_id = models.UUIDField(null=True, blank=True)
    content = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)

    class Meta:
        db_table = "notifications"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient", "-created_at"], name="idx_notif_recipient_created"),
            models.Index(fields=["recipient", "is_read"], name="idx_notif_recipient_read"),
        ]
