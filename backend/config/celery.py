"""Khởi tạo Celery Worker: nhận tác vụ nền qua Redis Broker (nén ảnh WebP, gửi email OTP, dọn tệp tạm)."""

import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

app = Celery("nhom1_social")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    # Quét dọn tệp tải lên tạm thời còn sót lại (ví dụ worker bị dừng giữa chừng)
    "cleanup-temp-uploads-hourly": {
        "task": "apps.media_files.tasks.cleanup_temp_uploads",
        "schedule": crontab(minute=0),
    },
}
