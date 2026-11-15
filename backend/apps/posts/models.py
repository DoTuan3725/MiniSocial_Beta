from django.conf import settings
from django.db import models

from common.models import BaseModel


class Post(BaseModel):
    """
    Bảng 5 - posts.
    - group_id: NULL nếu đăng trên trang cá nhân; lưu UUID nhóm (không FK chéo phân hệ).
    - privacy: PUBLIC | FRIENDS | PRIVATE (chỉ mình tôi), kiểm tra ở tầng Service.
    - Bộ đếm likes/comments/shares lưu sẵn, cập nhật nguyên tử bằng F() -> đọc feed không cần COUNT.
    - deleted_at: xóa mềm (giữ dữ liệu thống kê, phục vụ kiểm duyệt).
    - is_flagged: bị bộ lọc từ cấm gắn cờ -> ẩn với người khác cho tới khi Admin xử lý.
    """

    class Privacy(models.TextChoices):
        PUBLIC = "PUBLIC", "Công khai"
        FRIENDS = "FRIENDS", "Bạn bè"
        PRIVATE = "PRIVATE", "Chỉ mình tôi"

    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="posts")
    group_id = models.UUIDField(null=True, blank=True)
    content = models.TextField(blank=True, default="")
    privacy = models.CharField(max_length=10, choices=Privacy.choices, default=Privacy.PUBLIC)
    likes_count = models.PositiveIntegerField(default=0)
    comments_count = models.PositiveIntegerField(default=0)
    shares_count = models.PositiveIntegerField(default=0)
    is_pinned = models.BooleanField(default=False)
    is_flagged = models.BooleanField(default=False)
    is_edited = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "posts"
        ordering = ["-created_at"]
        indexes = [
            # Composite index phục vụ Feed: WHERE author_id IN (...) ORDER BY created_at DESC
            models.Index(fields=["author", "-created_at"], name="idx_post_author_created"),
            models.Index(fields=["group_id", "-created_at"], name="idx_post_group_created"),
            models.Index(fields=["-created_at", "-id"], name="idx_post_created_id"),
        ]


class Comment(BaseModel):
    """Bảng 7 - comments: bình luận đa cấp qua parent_id tự tham chiếu."""

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comments")
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.CASCADE, related_name="replies")
    content = models.TextField()
    is_edited = models.BooleanField(default=False)

    class Meta:
        db_table = "comments"
        ordering = ["created_at"]
        indexes = [models.Index(fields=["post", "created_at"], name="idx_comment_post_created")]


class Like(BaseModel):
    """Bảng 8 - likes: UNIQUE(post, user) bảo đảm mỗi người chỉ thích 1 lần."""

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="likes")

    class Meta:
        db_table = "likes"
        constraints = [models.UniqueConstraint(fields=["post", "user"], name="uq_like_post_user")]


class Share(BaseModel):
    """Bảng 9 - shares: chia sẻ bài viết lên trang cá nhân kèm lời dẫn."""

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="shares")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="shares")
    shared_content = models.TextField(blank=True, default="")

    class Meta:
        db_table = "shares"
        ordering = ["-created_at"]
