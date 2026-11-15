import logging

from celery import shared_task

from .emails import build_otp_email, send_email

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def send_otp_email(self, email, code, purpose):
    subject, html = build_otp_email(code, purpose)
    try:
        result = send_email(email, subject, html)
        if result.get("mock"):
            logger.warning("[DEV OTP] %s -> %s: %s", purpose, email, code)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.exception("Gửi email OTP thất bại")
        raise self.retry(exc=exc)
