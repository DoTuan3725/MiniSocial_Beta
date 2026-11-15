from django.apps import AppConfig


class MediaFilesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.media_files"
    label = "media_files"
    verbose_name = "4. Media (Pillow WebP + Cloudflare R2)"
