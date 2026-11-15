from django.conf import settings
from django.db import models

from common.models import BaseModel


class Report(BaseModel):
    """
    Bảng 16 - reports: báo cáo vi phạm đa hình (POST | COMMENT | USER).
    - reporter NULL + is_auto=True: do bộ lọc từ cấm tự tạo.
    - Quy trình: PENDING -> RESOLVED (kèm action_taken) | REJECTED.
    """

    class TargetType(models.TextChoices):
        POST = "POST", "Bài viết"
        COMMENT = "COMMENT", "Bình luận"
        USER = "USER", "Người dùng"

    class Reason(models.TextChoices):
        SPAM = "SPAM", "Spam / quảng cáo"
        HARASSMENT = "HARASSMENT", "Quấy rối / bắt nạt"
        HATE_SPEECH = "HATE_SPEECH", "Ngôn từ thù ghét"
        VIOLENCE = "VIOLENCE", "Bạo lực"
        NUDITY = "NUDITY", "Nội dung khỏa thân / tình dục"
        FALSE_INFO = "FALSE_INFO", "Thông tin sai sự thật"
        OFFENSIVE_LANGUAGE = "OFFENSIVE_LANGUAGE", "Ngôn từ thô tục"
        OTHER = "OTHER", "Khác"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Chờ xử lý"
        RESOLVED = "RESOLVED", "Đã xử lý"
        REJECTED = "REJECTED", "Bác bỏ"

    class Action(models.TextChoices):
        NONE = "NONE", "Không áp dụng"
        DELETE_CONTENT = "DELETE_CONTENT", "Gỡ nội dung"
        WARN_USER = "WARN_USER", "Cảnh cáo"
        BAN_USER = "BAN_USER", "Khóa tài khoản"

    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="filed_reports"
    )
    is_auto = models.BooleanField(default=False)
    target_type = models.CharField(max_length=10, choices=TargetType.choices)
    target_id = models.UUIDField()
    reported_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="received_reports"
    )
    reason = models.CharField(max_length=20, choices=Reason.choices, default=Reason.OTHER)
    details = models.TextField(blank=True, default="")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    action_taken = models.CharField(max_length=20, choices=Action.choices, default=Action.NONE)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="handled_reports"
    )
    resolution_notes = models.TextField(blank=True, default="")
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "reports"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "-created_at"], name="idx_report_status_created"),
            models.Index(fields=["target_type", "target_id"], name="idx_report_target"),
        ]
