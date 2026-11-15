from django.apps import AppConfig


class PostsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.posts"
    label = "posts"
    verbose_name = "3. Bài viết & Bảng tin"

    def ready(self):
        from . import listeners  # noqa: F401
