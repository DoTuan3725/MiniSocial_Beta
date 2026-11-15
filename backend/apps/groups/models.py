from django.conf import settings
from django.db import models

from common.models import BaseModel
from common.text import unaccent


class Group(BaseModel):
    """Bảng 10 - groups. PUBLIC: ai cũng xem & vào ngay. PRIVATE: phải được duyệt mới xem bài."""

    class Privacy(models.TextChoices):
        PUBLIC = "PUBLIC", "Công khai"
        PRIVATE = "PRIVATE", "Nhóm kín"

    name = models.CharField(max_length=100)
    search_name = models.CharField(max_length=100, blank=True, default="", db_index=True)
    description = models.TextField(blank=True, default="")
    cover_url = models.CharField(max_length=500, blank=True, default="")
    privacy = models.CharField(max_length=10, choices=Privacy.choices, default=Privacy.PUBLIC)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="created_groups")

    class Meta:
        db_table = "groups"
        verbose_name = "Nhóm"
        verbose_name_plural = "Nhóm"

    def save(self, *args, **kwargs):
        self.search_name = unaccent(self.name)
        super().save(*args, **kwargs)


class GroupMember(BaseModel):
    """
    Bảng 11 - group_members.
    role (RBAC): ADMIN > MOD > MEMBER.
    status (máy trạng thái): PENDING -> ACCEPTED | REJECTED.
    """

    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Quản trị viên"
        MOD = "MOD", "Kiểm duyệt viên"
        MEMBER = "MEMBER", "Thành viên"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Chờ duyệt"
        ACCEPTED = "ACCEPTED", "Thành viên"
        REJECTED = "REJECTED", "Bị từ chối"

    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="members")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="group_memberships")
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.MEMBER)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    joined_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "group_members"
        constraints = [models.UniqueConstraint(fields=["group", "user"], name="uq_group_member")]
        indexes = [models.Index(fields=["group", "status"], name="idx_gm_group_status")]
