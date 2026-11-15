from django.conf import settings
from django.db import models

from common.models import BaseModel


class Conversation(BaseModel):
    """Bảng 12 - conversations: DIRECT (1-1) hoặc GROUP (nhóm chat)."""

    class Type(models.TextChoices):
        DIRECT = "DIRECT", "Chat 1-1"
        GROUP = "GROUP", "Chat nhóm"

    type = models.CharField(max_length=10, choices=Type.choices, default=Type.DIRECT)
    title = models.CharField(max_length=100, blank=True, default="")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="created_conversations"
    )
    last_message_at = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        db_table = "conversations"


class ConversationMember(BaseModel):
    """Bảng 13 - conversation_members. last_read_at dùng để tính tin chưa đọc & trạng thái 'đã xem'."""

    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Quản trị nhóm chat"
        MEMBER = "MEMBER", "Thành viên"

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="members")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="conversation_memberships"
    )
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.MEMBER)
    last_read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "conversation_members"
        constraints = [models.UniqueConstraint(fields=["conversation", "user"], name="uq_conversation_member")]


class Message(BaseModel):
    """Bảng 14 - messages. Index (conversation, created_at) phục vụ phân trang con trỏ khi cuộn lên."""

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="messages")
    content = models.TextField(blank=True, default="")
    file_url = models.CharField(max_length=500, blank=True, default="")
    file_type = models.CharField(max_length=10, blank=True, default="")  # IMAGE | VIDEO

    class Meta:
        db_table = "messages"
        indexes = [models.Index(fields=["conversation", "-created_at"], name="idx_msg_conv_created")]
