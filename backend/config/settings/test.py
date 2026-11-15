"""Cấu hình chạy pytest: SQLite/MySQL + fakeredis + channel layer trong RAM + Celery eager."""

from .base import *  # noqa: F401,F403
from .base import BASE_DIR, DB_ENGINE

DEBUG = False
ALLOWED_HOSTS = ["*"]
if DB_ENGINE == "sqlite":
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
STORAGE_BACKEND = "local"
MEDIA_ROOT = BASE_DIR / "test_media"
TEMP_UPLOAD_DIR = BASE_DIR / "test_tmp_uploads"
MEDIA_PUBLIC_BASE_URL = "http://testserver/media"
RESEND_API_KEY = ""
REST_FRAMEWORK = {  # noqa: F405
    **REST_FRAMEWORK,  # noqa: F405
    "DEFAULT_THROTTLE_CLASSES": [],
    "DEFAULT_THROTTLE_RATES": {"anon": "10000/min", "user": "10000/min", "auth": "10000/min", "otp": "10000/min"},
}
LOG_JSON = False
LOGGING = {"version": 1, "disable_existing_loggers": False}
