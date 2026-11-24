"""
Cấu hình dùng chung cho mọi môi trường.
Biến môi trường được đọc từ tệp .env (không commit lên Git) hoặc từ Docker Compose.
"""

import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR.parent / ".env")
load_dotenv(BASE_DIR / ".env")


def env(name, default=None):
    return os.getenv(name, default)


def env_bool(name, default=False):
    return str(os.getenv(name, str(default))).lower() in ("1", "true", "yes", "on")


def env_list(name, default=""):
    return [x.strip() for x in os.getenv(name, default).split(",") if x.strip()]


SECRET_KEY = env("SECRET_KEY", "dev-only-insecure-key-change-me")
DEBUG = env_bool("DEBUG", False)
ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "localhost,127.0.0.1")

INSTALLED_APPS = [
    "daphne",  # Daphne phải đứng đầu để runserver chạy bằng ASGI
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Thư viện bên thứ ba
    "rest_framework",
    "corsheaders",
    "channels",
    "drf_spectacular",
    # 8 phân hệ Modular Monolith
    "apps.authentication.apps.AuthenticationConfig",
    "apps.users.apps.UsersConfig",
    "apps.posts.apps.PostsConfig",
    "apps.media_files.apps.MediaFilesConfig",
    "apps.chat.apps.ChatConfig",
    "apps.notifications.apps.NotificationsConfig",
    "apps.groups.apps.GroupsConfig",
    "apps.admin_management.apps.AdminManagementConfig",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
ASGI_APPLICATION = "config.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# ---------------------------------------------------------------- Database
DB_ENGINE = env("DB_ENGINE", "mysql")
if DB_ENGINE == "sqlite":
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": env("DB_NAME", "social_db"),
            "USER": env("DB_USER", "social_user"),
            "PASSWORD": env("DB_PASSWORD", ""),
            "HOST": env("DB_HOST", "127.0.0.1"),
            "PORT": env("DB_PORT", "3306"),
            "CONN_MAX_AGE": int(env("DB_CONN_MAX_AGE", "60")),
            "OPTIONS": {
                "charset": "utf8mb4",
                "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
            },
            "TEST": {"CHARSET": "utf8mb4", "COLLATION": "utf8mb4_unicode_ci"},
        }
    }

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "authentication.User"

# Argon2id: chống bẻ khóa bằng GPU, salt riêng cho từng mật khẩu
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "apps.authentication.validators.StrongPasswordValidator"},
]

# ---------------------------------------------------------------- Redis
REDIS_URL = env("REDIS_URL", "redis://127.0.0.1:6379/0")
CELERY_BROKER_URL = env("CELERY_BROKER_URL", "redis://127.0.0.1:6379/1")
CHANNEL_REDIS_URL = env("CHANNEL_REDIS_URL", "redis://127.0.0.1:6379/2")

CACHES = {"default": {"BACKEND": "django.core.cache.backends.redis.RedisCache", "LOCATION": REDIS_URL}}

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [CHANNEL_REDIS_URL], "capacity": 1500, "expiry": 10},
    }
}

CELERY_TASK_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_ALWAYS_EAGER = env_bool("CELERY_TASK_ALWAYS_EAGER", False)
CELERY_TASK_ACKS_LATE = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_TIMEZONE = "Asia/Ho_Chi_Minh"

# ---------------------------------------------------------------- DRF & JWT
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["apps.authentication.authentication.RedisJWTAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_SCHEMA_CLASS": "common.schema.ApiAutoSchema",
    "EXCEPTION_HANDLER": "common.exceptions.api_exception_handler",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": env("THROTTLE_ANON", "100/min"),
        "user": env("THROTTLE_USER", "300/min"),
        "auth": env("THROTTLE_AUTH", "10/min"),
        "otp": env("THROTTLE_OTP", "5/min"),
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=int(env("JWT_ACCESS_MINUTES", "15"))),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=int(env("JWT_REFRESH_DAYS", "7"))),
    "ALGORITHM": "HS256",
    "SIGNING_KEY": env("JWT_SIGNING_KEY", SECRET_KEY),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "UPDATE_LAST_LOGIN": False,
}

REFRESH_COOKIE_NAME = "refresh_token"
REFRESH_COOKIE_PATH = "/api/v1/auth/"
REFRESH_COOKIE_SECURE = env_bool("REFRESH_COOKIE_SECURE", not DEBUG)
REFRESH_COOKIE_SAMESITE = env("REFRESH_COOKIE_SAMESITE", "Strict")
REFRESH_COOKIE_DOMAIN = env("REFRESH_COOKIE_DOMAIN") or None

# ---------------------------------------------------------------- OTP & Email (Resend)
OTP_TTL_SECONDS = 300
OTP_RESEND_COOLDOWN_SECONDS = 60
OTP_MAX_ATTEMPTS = 5
LOGIN_MAX_FAILURES = 5
LOGIN_LOCK_SECONDS = 15 * 60

RESEND_API_KEY = env("RESEND_API_KEY", "")
EMAIL_FROM = env("EMAIL_FROM", "MiniSocial <onboarding@resend.dev>")
APP_NAME = env("APP_NAME", "MiniSocial")

# ---------------------------------------------------------------- CORS
CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS", "http://localhost,http://localhost:5173")
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS

# ---------------------------------------------------------------- Media / Object storage
STORAGE_BACKEND = env("STORAGE_BACKEND", "s3")  # s3 (MinIO/R2) | local
S3_ENDPOINT_URL = env("S3_ENDPOINT_URL", "http://minio:9000")
S3_ACCESS_KEY = env("S3_ACCESS_KEY", "")
S3_SECRET_KEY = env("S3_SECRET_KEY", "")
S3_BUCKET = env("S3_BUCKET", "social-media")
S3_REGION = env("S3_REGION", "auto")
MEDIA_PUBLIC_BASE_URL = env("MEDIA_PUBLIC_BASE_URL", "http://localhost:9000/social-media")
MEDIA_ROOT = BASE_DIR / "media"
MEDIA_URL = "/media/"
TEMP_UPLOAD_DIR = Path(env("TEMP_UPLOAD_DIR", str(BASE_DIR / "tmp_uploads")))
MAX_UPLOAD_MB = int(env("MAX_UPLOAD_MB", "10"))
MAX_FILES_PER_POST = 10
FILE_UPLOAD_MAX_MEMORY_SIZE = 2 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 12 * 1024 * 1024

# ---------------------------------------------------------------- Misc
FEED_CACHE_TTL = int(env("FEED_CACHE_TTL", "120"))
PRESENCE_TTL_SECONDS = 70

SPECTACULAR_SETTINGS = {
    "TITLE": "Mạng Xã Hội Mini API - Nhóm 1",
    "DESCRIPTION": "REST API cho 28 Use Case. WebSocket: xem docs/WEBSOCKET.md.",
    "VERSION": "2.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
}

LANGUAGE_CODE = "vi"
TIME_ZONE = "Asia/Ho_Chi_Minh"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# ---------------------------------------------------------------- Logging (JSON có cấu trúc - NFR-LOG-01)
LOG_LEVEL = env("LOG_LEVEL", "INFO")
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "pythonjsonlogger.json.JsonFormatter",
            "fmt": "%(asctime)s %(levelname)s %(name)s %(message)s",
        },
        "plain": {"format": "%(asctime)s %(levelname)s %(name)s: %(message)s"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json" if env_bool("LOG_JSON", True) else "plain",
        }
    },
    "root": {"handlers": ["console"], "level": LOG_LEVEL},
    "loggers": {"django.db.backends": {"level": "WARNING"}},
}

# ---------------------------------------------------------------- Sentry (bắt lỗi 500 tự động)
SENTRY_DSN = env("SENTRY_DSN", "")
if SENTRY_DSN:  # pragma: no cover
    import sentry_sdk
    from sentry_sdk.integrations.celery import CeleryIntegration
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration(), CeleryIntegration()],
        environment=env("SENTRY_ENVIRONMENT", "production"),
        traces_sample_rate=float(env("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
        send_default_pii=False,
    )
