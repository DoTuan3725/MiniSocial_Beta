"""
AUTH SERVICE - giao diện công khai của phân hệ Auth.
Phân hệ khác chỉ được gọi qua module này, không import models.
"""

import logging
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.db.models import Q
from django.db.models.expressions import RawSQL
from django.utils import timezone

from common import events
from common.exceptions import NotFound, ServiceError
from common.redis_client import get_redis
from common.stats import count_per_day
from common.text import sanitize_text, unaccent

from . import otp, tokens
from .models import User
from .tasks import send_otp_email

logger = logging.getLogger(__name__)


def _validate_password(password, user=None):
    try:
        validate_password(password, user)
    except DjangoValidationError as exc:
        raise ServiceError("Mật khẩu chưa đủ mạnh", errors={"password": list(exc.messages)})


def _send_otp(purpose, email):
    code = otp.create_otp(purpose, email)
    send_otp_email.delay(email, code, purpose)
    return code


# ------------------------------------------------------------------ Đăng ký (UC-01)
@transaction.atomic
def register(email, password, full_name, birth_date=None):
    email = email.strip().lower()
    full_name = sanitize_text(full_name, 100)
    if not full_name:
        raise ServiceError("Họ tên không được để trống", errors={"full_name": ["Bắt buộc"]})
    existing = User.objects.filter(email=email).first()
    if existing and existing.email_verified:
        raise ServiceError("Email đã được sử dụng", errors={"email": ["Email đã tồn tại"]}, code="EMAIL_EXISTS")
    _validate_password(password)
    if existing:  # đăng ký lại khi chưa kích hoạt -> cập nhật thông tin và gửi lại OTP
        user = existing
        user.full_name = full_name
        user.set_password(password)
        user.save()
    else:
        user = User.objects.create_user(email=email, password=password, full_name=full_name)
    events.publish(
        events.USER_REGISTERED, user_id=str(user.id), birth_date=birth_date.isoformat() if birth_date else None
    )
    _send_otp(otp.PURPOSE_REGISTER, email)
    return user


def verify_email(email, code):
    email = email.strip().lower()
    user = User.objects.filter(email=email).first()
    if not user:
        raise NotFound("Không tìm thấy tài khoản")
    otp.verify_otp(otp.PURPOSE_REGISTER, email, code)
    if not user.email_verified:
        user.email_verified = True
        user.save(update_fields=["email_verified"])
    _ensure_can_login(user)
    return user


def request_otp(email, purpose):
    """Gửi OTP cho 3 luồng. Với LOGIN/RESET không tiết lộ email có tồn tại hay không."""
    email = email.strip().lower()
    user = User.objects.filter(email=email).first()
    if purpose == otp.PURPOSE_REGISTER:
        if not user:
            raise NotFound("Email chưa đăng ký")
        if user.email_verified:
            raise ServiceError("Tài khoản đã được kích hoạt, hãy đăng nhập.", code="ALREADY_VERIFIED")
        return _send_otp(purpose, email)
    if user and user.is_active and (user.email_verified or purpose == otp.PURPOSE_RESET):
        return _send_otp(purpose, email)
    # Vẫn áp cooldown để không lộ thông tin qua thời gian phản hồi
    if otp.cooldown_remaining(purpose, email):
        otp.create_otp(purpose, email)
    return None


# ------------------------------------------------------------------ Đăng nhập (UC-02, UC-03)
def _lock_key(email, ip):
    return f"login_fail:{ip}:{email}"


def _ensure_can_login(user):
    if not user.is_active:
        raise ServiceError("Tài khoản đã bị khóa do vi phạm tiêu chuẩn cộng đồng.", 403, "ACCOUNT_BANNED")
    if not user.email_verified:
        raise ServiceError(
            "Tài khoản chưa kích hoạt. Vui lòng nhập mã OTP đã gửi tới email.", 403, "EMAIL_NOT_VERIFIED"
        )


def login_with_password(email, password, ip="unknown"):
    email = email.strip().lower()
    r = get_redis()
    key = _lock_key(email, ip)
    fails = int(r.get(key) or 0)
    if fails >= settings.LOGIN_MAX_FAILURES:
        ttl = r.ttl(key)
        raise ServiceError(
            f"Đăng nhập sai quá {settings.LOGIN_MAX_FAILURES} lần. Thử lại sau {max(ttl, 0) // 60 + 1} phút.",
            429,
            "LOGIN_LOCKED",
        )
    user = User.objects.filter(email=email).first()
    if not user or not user.check_password(password):
        pipe = r.pipeline()
        pipe.incr(key)
        pipe.expire(key, settings.LOGIN_LOCK_SECONDS)
        pipe.execute()
        raise ServiceError("Email hoặc mật khẩu không chính xác", 401, "INVALID_CREDENTIALS")
    if not user.email_verified and user.is_active:
        try:
            _send_otp(otp.PURPOSE_REGISTER, email)
        except ServiceError:
            pass  # đang trong cooldown thì giữ mã cũ
    _ensure_can_login(user)
    r.delete(key)
    return user


def login_with_otp(email, code):
    email = email.strip().lower()
    user = User.objects.filter(email=email).first()
    otp.verify_otp(otp.PURPOSE_LOGIN, email, code)
    if not user:
        raise NotFound("Không tìm thấy tài khoản")
    _ensure_can_login(user)
    return user


# ------------------------------------------------------------------ Mật khẩu (UC-06)
def reset_password(email, code, new_password):
    email = email.strip().lower()
    user = User.objects.filter(email=email).first()
    if not user:
        raise NotFound("Không tìm thấy tài khoản")
    _validate_password(new_password, user)
    otp.verify_otp(otp.PURPOSE_RESET, email, code)
    user.set_password(new_password)
    if not user.email_verified:
        user.email_verified = True  # nhận được OTP qua email nghĩa là sở hữu email
    user.save()
    tokens.revoke_all_sessions(user.id)
    return user


def change_password(user, old_password, new_password):
    if not user.check_password(old_password):
        raise ServiceError("Mật khẩu hiện tại không đúng", errors={"old_password": ["Không đúng"]})
    _validate_password(new_password, user)
    user.set_password(new_password)
    user.save()
    tokens.revoke_all_sessions(user.id)
    return user


def get_active_user(user_id):
    user = User.objects.filter(id=user_id, is_active=True).first()
    if not user:
        raise ServiceError("Người dùng không tồn tại hoặc đã bị khóa", 401, "USER_INACTIVE")
    return user


# ------------------------------------------------------------------ Dành cho phân hệ khác
def user_queryset():
    """QuerySet người dùng đã kích hoạt, đang hoạt động (dùng cho tìm kiếm, gợi ý)."""
    return User.objects.filter(is_active=True, email_verified=True)


def search_user_ids(query, limit=20):
    """
    UC-08: tìm theo họ tên không dấu.
    MySQL: FULLTEXT INDEX (ngram parser) trên users.search_name -> MATCH ... AGAINST.
    SQLite (test): LIKE.
    """
    from django.db import connection

    term = unaccent(query)
    if not term:
        return []
    qs = user_queryset()
    if connection.vendor == "mysql":
        boolean_q = " ".join(f'"{w}"' for w in term.replace('"', " ").split())
        qs = (
            qs.annotate(score=RawSQL("MATCH(search_name) AGAINST (%s IN BOOLEAN MODE)", (boolean_q,)))
            .filter(score__gt=0)
            .order_by("-score")
        )
    else:
        cond = Q()
        for word in term.split():
            cond &= Q(search_name__icontains=word)
        qs = qs.filter(cond)
    if "@" in query:
        qs = user_queryset().filter(email__iexact=query.strip())
    return [str(i) for i in qs.values_list("id", flat=True)[:limit]]


def set_user_active(user_id, active):
    user = User.objects.filter(id=user_id).first()
    if not user:
        raise NotFound("Không tìm thấy người dùng")
    if user.role == User.Role.ADMIN and not active:
        raise ServiceError("Không thể khóa tài khoản Quản trị viên")
    user.is_active = active
    user.save(update_fields=["is_active"])
    if not active:
        tokens.revoke_all_sessions(user.id)
    return user


def admin_user_queryset(query=None, status=None):
    qs = User.objects.all().order_by("-created_at")
    if query:
        term = unaccent(query)
        qs = qs.filter(Q(search_name__icontains=term) | Q(email__icontains=query.strip()))
    if status == "banned":
        qs = qs.filter(is_active=False)
    elif status == "active":
        qs = qs.filter(is_active=True, email_verified=True)
    elif status == "unverified":
        qs = qs.filter(email_verified=False)
    return qs


def user_stats(days=14):
    now = timezone.now()
    today = timezone.localtime(now).replace(hour=0, minute=0, second=0, microsecond=0)
    return {
        "total_users": User.objects.count(),
        "verified_users": User.objects.filter(email_verified=True).count(),
        "banned_users": User.objects.filter(is_active=False).count(),
        "dau": User.objects.filter(last_login__gte=today).count(),
        "mau": User.objects.filter(last_login__gte=now - timedelta(days=30)).count(),
        "new_users_per_day": count_per_day(User.objects.all(), days=days),
    }
