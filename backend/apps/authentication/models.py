from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

from common.models import BaseModel
from common.text import unaccent


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra):
        if not email:
            raise ValueError("Email là bắt buộc")
        user = self.model(email=self.normalize_email(email).lower(), **extra)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        extra.setdefault("role", User.Role.ADMIN)
        extra.setdefault("email_verified", True)
        return self.create_user(email, password, **extra)


class User(AbstractBaseUser, PermissionsMixin, BaseModel):
    """
    Bảng 1 - users: tài khoản đăng nhập.
    - email_verified: đã kích hoạt bằng OTP chưa (UC-01).
    - is_active: False khi bị Admin khóa (UC-28). Tách riêng 2 cờ để báo lỗi đăng nhập đúng nghĩa.
    - search_name: họ tên không dấu, có FULLTEXT INDEX (ngram) trên MySQL để tìm kiếm (UC-08).
    """

    class Role(models.TextChoices):
        USER = "USER", "Người dùng"
        ADMIN = "ADMIN", "Quản trị viên"

    email = models.EmailField(max_length=255, unique=True)
    full_name = models.CharField(max_length=100)
    search_name = models.CharField(max_length=100, blank=True, default="")
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.USER)
    email_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    class Meta:
        db_table = "users"
        ordering = ["-created_at"]
        verbose_name = "Người dùng"
        verbose_name_plural = "Người dùng"

    def save(self, *args, **kwargs):
        self.search_name = unaccent(self.full_name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name} <{self.email}>"
