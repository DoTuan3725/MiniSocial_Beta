"""Gửi email giao dịch qua Resend API. Không có RESEND_API_KEY thì in mã ra log (chế độ dev)."""

import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

SUBJECTS = {
    "register": "Mã kích hoạt tài khoản",
    "login": "Mã đăng nhập",
    "reset": "Mã đặt lại mật khẩu",
}


def build_otp_email(code, purpose):
    action = {
        "register": "kích hoạt tài khoản",
        "login": "đăng nhập",
        "reset": "đặt lại mật khẩu",
    }.get(purpose, "xác thực")
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:480px;margin:auto;padding:24px;
                border:1px solid #e3e8ef;border-radius:12px">
      <h2 style="color:#1F3A5F;margin:0 0 12px">{settings.APP_NAME}</h2>
      <p>Mã {action} của bạn là:</p>
      <p style="font-size:32px;letter-spacing:8px;font-weight:bold;color:#1F3A5F;margin:16px 0">{code}</p>
      <p style="color:#6B7785">Mã có hiệu lực trong 5 phút. Không chia sẻ mã này cho bất kỳ ai.</p>
      <p style="color:#6B7785;font-size:12px">Nếu bạn không yêu cầu, hãy bỏ qua email này.</p>
    </div>"""
    return f"[{settings.APP_NAME}] {SUBJECTS.get(purpose, 'Mã xác thực')}: {code}", html


def send_email(to, subject, html):
    if not settings.RESEND_API_KEY:
        logger.warning("RESEND_API_KEY trống - bỏ qua gửi mail thật. To=%s Subject=%s", to, subject)
        return {"mock": True}
    resp = requests.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {settings.RESEND_API_KEY}", "Content-Type": "application/json"},
        json={"from": settings.EMAIL_FROM, "to": [to], "subject": subject, "html": html},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()
