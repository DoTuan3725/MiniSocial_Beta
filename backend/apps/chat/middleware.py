"""
Xác thực JWT ngay tại bước bắt tay WebSocket.
Trình duyệt không gửi được header Authorization cho WebSocket nên access token đi qua query string:
    wss://domain/ws/chat/?token=<access_token>
"""

from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken

from apps.authentication.tokens import is_access_revoked


@database_sync_to_async
def user_from_token(raw):
    try:
        token = AccessToken(raw)
    except TokenError:
        return AnonymousUser()
    if is_access_revoked(token):
        return AnonymousUser()
    user = get_user_model().objects.filter(id=token["user_id"], is_active=True).first()
    return user or AnonymousUser()


class JwtQueryAuthMiddleware:
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        params = parse_qs(scope.get("query_string", b"").decode())
        token = (params.get("token") or [None])[0]
        scope["user"] = await user_from_token(token) if token else AnonymousUser()
        return await self.inner(scope, receive, send)
