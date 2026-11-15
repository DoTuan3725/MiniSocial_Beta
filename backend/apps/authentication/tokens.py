"""
Quản lý JWT (SimpleJWT) + Redis:
- Access token 15 phút (trả trong body, frontend giữ trong RAM).
- Refresh token 7 ngày (HttpOnly Cookie). Mỗi refresh token có jti được ghi vào Redis (whitelist).
- Token Rotation: mỗi lần refresh -> xóa jti cũ, cấp cặp mới.
  Nếu jti cũ bị dùng lại (đã bị xoay vòng) -> nghi bị đánh cắp -> thu hồi TOÀN BỘ phiên của user.
- Blacklist access token khi đăng xuất: bl:<jti> sống đến khi token hết hạn.
"""

import time

from django.conf import settings
from django.utils import timezone
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from common.exceptions import ServiceError
from common.redis_client import get_redis


def _refresh_ttl():
    return int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds())


def _access_ttl():
    return int(settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds())


def issue_tokens(user):
    refresh = RefreshToken.for_user(user)
    access = refresh.access_token
    access["role"] = user.role
    access["full_name"] = user.full_name
    r = get_redis()
    uid = str(user.id)
    pipe = r.pipeline()
    pipe.set(f"rt:{refresh['jti']}", uid, ex=_refresh_ttl())
    pipe.sadd(f"user_rt:{uid}", refresh["jti"])
    pipe.expire(f"user_rt:{uid}", _refresh_ttl())
    pipe.execute()
    user.last_login = timezone.now()
    user.save(update_fields=["last_login"])
    return str(access), str(refresh)


def rotate_refresh(refresh_str):
    try:
        token = RefreshToken(refresh_str)
    except TokenError:
        raise ServiceError("Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại.", 401, "REFRESH_INVALID")
    jti, uid = token["jti"], token["user_id"]
    r = get_redis()
    if r.getdel(f"rt:{jti}") is None:
        # Refresh token hợp lệ về chữ ký nhưng đã bị xoay vòng/thu hồi -> phát hiện tái sử dụng
        revoke_all_sessions(uid)
        raise ServiceError("Phát hiện phiên đăng nhập bất thường. Vui lòng đăng nhập lại.", 401, "REFRESH_REUSED")
    r.srem(f"user_rt:{uid}", jti)
    return uid


def revoke_refresh(refresh_str):
    try:
        token = RefreshToken(refresh_str)
    except TokenError:
        return
    r = get_redis()
    r.delete(f"rt:{token['jti']}")
    r.srem(f"user_rt:{token['user_id']}", token["jti"])


def blacklist_access(access_str):
    try:
        token = AccessToken(access_str)
    except TokenError:
        return
    remaining = int(token["exp"] - time.time())
    if remaining > 0:
        get_redis().set(f"bl:{token['jti']}", 1, ex=remaining)


def revoke_all_sessions(user_id):
    """Thu hồi mọi refresh token + vô hiệu mọi access token đã cấp trước thời điểm này."""
    r = get_redis()
    uid = str(user_id)
    jtis = r.smembers(f"user_rt:{uid}")
    pipe = r.pipeline()
    for jti in jtis:
        pipe.delete(f"rt:{jti}")
    pipe.delete(f"user_rt:{uid}")
    pipe.set(f"revoked_before:{uid}", int(time.time()), ex=_access_ttl())
    pipe.execute()


def is_access_revoked(token):
    r = get_redis()
    if r.exists(f"bl:{token['jti']}"):
        return True
    revoked_before = r.get(f"revoked_before:{token['user_id']}")
    return bool(revoked_before and int(token.get("iat", 0)) <= int(revoked_before))
