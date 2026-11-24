from django.apps import AppConfig


class AuthenticationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.authentication"
    label = "authentication"
    verbose_name = "1. Xác thực & Danh tính"

    def ready(self):
        from . import schema  # noqa: F401  (đăng ký Bearer JWT cho Swagger)
