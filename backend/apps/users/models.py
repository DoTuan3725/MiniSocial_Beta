from django.conf import settings
from django.db import models

from common.models import BaseModel


class Profile(BaseModel):
    """Bảng 2 - profiles: hồ sơ cá nhân, quan hệ 1-1 với users."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    avatar_url = models.CharField(max_length=500, blank=True, default="")
    cover_url = models.CharField(max_length=500, blank=True, default="")
    bio = models.TextField(blank=True, default="")
    location = models.CharField(max_length=100, blank=True, default="")
    birth_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "profiles"
        verbose_name = "Hồ sơ"
        verbose_name_plural = "Hồ sơ"


class Friendship(BaseModel):
    """
    Bảng 3 - friendships. Máy trạng thái:
        NONE (không có dòng) -> PENDING (gửi lời mời) -> ACCEPTED (bạn bè)
        PENDING --từ chối/hủy--> NONE ; ACCEPTED --hủy kết bạn--> NONE
    Mỗi cặp người dùng chỉ có tối đa 1 dòng (kiểm tra 2 chiều ở tầng Service).
    """

    class Status(models.TextChoices):
        PENDING = "PENDING", "Chờ phản hồi"
        ACCEPTED = "ACCEPTED", "Bạn bè"

    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_friendships")
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="received_friendships"
    )
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)

    class Meta:
        db_table = "friendships"
        constraints = [
            models.UniqueConstraint(fields=["sender", "receiver"], name="uq_friendship_pair"),
            models.CheckConstraint(condition=~models.Q(sender=models.F("receiver")), name="ck_friendship_not_self"),
        ]
        indexes = [
            models.Index(fields=["receiver", "status"], name="idx_friend_receiver_status"),
            models.Index(fields=["sender", "status"], name="idx_friend_sender_status"),
        ]


class Block(BaseModel):
    """Bảng 4 - blocks: chặn 2 chiều (không thấy nhau, không nhắn tin, không kết bạn)."""

    blocker = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="blocking")
    blocked = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="blocked_by")

    class Meta:
        db_table = "blocks"
        constraints = [
            models.UniqueConstraint(fields=["blocker", "blocked"], name="uq_block_pair"),
            models.CheckConstraint(condition=~models.Q(blocker=models.F("blocked")), name="ck_block_not_self"),
        ]
