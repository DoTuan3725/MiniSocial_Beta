from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken

from .tokens import is_access_revoked


class RedisJWTAuthentication(JWTAuthentication):
    """
    Đọc 'Authorization: Bearer <access>'. Ngoài kiểm tra chữ ký/hạn dùng của SimpleJWT,
    còn từ chối token nằm trong Redis blacklist hoặc đã bị thu hồi (đăng xuất, đổi mật khẩu, bị khóa).
    SimpleJWT tự từ chối user có is_active=False.
    """

    def get_validated_token(self, raw_token):
        token = super().get_validated_token(raw_token)
        if is_access_revoked(token):
            raise InvalidToken("Phiên đăng nhập đã bị thu hồi")
        return token
