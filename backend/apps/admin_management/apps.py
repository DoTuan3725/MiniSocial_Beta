from django.apps import AppConfig


class AdminManagementConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.admin_management"
    label = "admin_management"
    verbose_name = "8. Quản trị & Kiểm duyệt"

    def ready(self):
        from . import listeners  # noqa: F401
