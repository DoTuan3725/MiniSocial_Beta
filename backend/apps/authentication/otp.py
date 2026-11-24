"""
Mã OTP 6 chữ số lưu trong Redis (In-Memory):
  otp:<purpose>:<email>      -> hash {code_hash, attempts}   TTL 300s
  otp_cd:<purpose>:<email>   -> khóa chống spam gửi lại        TTL 60s
Chỉ lưu HMAC của mã (không lưu bản rõ), sai quá 5 lần thì hủy mã.
"""

import hashlib
import hmac
import secrets

from django.conf import settings

from common.exceptions import ServiceError
from common.redis_client import get_redis

PURPOSE_REGISTER = "register"
PURPOSE_LOGIN = "login"
PURPOSE_RESET = "reset"
PURPOSES = {PURPOSE_REGISTER, PURPOSE_LOGIN, PURPOSE_RESET}


def _hash(code):
    return hmac.new(settings.SECRET_KEY.encode(), code.encode(), hashlib.sha256).hexdigest()


def _key(purpose, email):
    return f"otp:{purpose}:{email.lower()}"


def _cd_key(purpose, email):
    return f"otp_cd:{purpose}:{email.lower()}"


def cooldown_remaining(purpose, email):
    ttl = get_redis().ttl(_cd_key(purpose, email))
    return ttl if ttl and ttl > 0 else 0


def create_otp(purpose, email):
    if purpose not in PURPOSES:
        raise ServiceError("Mục đích OTP không hợp lệ")
    remaining = cooldown_remaining(purpose, email)
    if remaining:
        raise ServiceError(
            f"Vui lòng đợi {remaining} giây trước khi yêu cầu mã mới.",
            status_code=429,
            code="OTP_COOLDOWN",
            errors={"retry_after": remaining},
        )
    code = f"{secrets.randbelow(10**6):06d}"
    r = get_redis()
    pipe = r.pipeline()
    pipe.delete(_key(purpose, email))
    pipe.hset(_key(purpose, email), mapping={"code_hash": _hash(code), "attempts": 0})
    pipe.expire(_key(purpose, email), settings.OTP_TTL_SECONDS)
    pipe.set(_cd_key(purpose, email), 1, ex=settings.OTP_RESEND_COOLDOWN_SECONDS)
    pipe.execute()
    return code


def verify_otp(purpose, email, code):
    r = get_redis()
    key = _key(purpose, email)
    data = r.hgetall(key)
    if not data:
        raise ServiceError("Mã OTP đã hết hạn hoặc không tồn tại. Vui lòng yêu cầu mã mới.", code="OTP_EXPIRED")
    if hmac.compare_digest(data.get("code_hash", ""), _hash(str(code).strip())):
        r.delete(key)
        return True
    attempts = r.hincrby(key, "attempts", 1)
    if attempts >= settings.OTP_MAX_ATTEMPTS:
        r.delete(key)
        raise ServiceError("Nhập sai quá nhiều lần, mã OTP đã bị hủy. Vui lòng yêu cầu mã mới.", code="OTP_LOCKED")
    raise ServiceError(
        f"Mã OTP không đúng. Bạn còn {settings.OTP_MAX_ATTEMPTS - attempts} lần thử.", code="OTP_INVALID"
    )
