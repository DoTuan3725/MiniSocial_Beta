from django.conf import settings
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from common.exceptions import ServiceError
from common.responses import api_error, api_success

from . import services, tokens
from .serializers import (
    ChangePasswordSerializer,
    EmailSerializer,
    LoginSerializer,
    MeSerializer,
    OtpRequestSerializer,
    OtpVerifySerializer,
    RegisterSerializer,
    ResetPasswordSerializer,
)


def client_ip(request):
    return (
        request.META.get("HTTP_CF_CONNECTING_IP")
        or request.META.get("HTTP_X_REAL_IP")
        or request.META.get("REMOTE_ADDR", "unknown")
    )


def set_refresh_cookie(response, refresh):
    response.set_cookie(
        settings.REFRESH_COOKIE_NAME,
        refresh,
        max_age=int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds()),
        httponly=True,
        secure=settings.REFRESH_COOKIE_SECURE,
        samesite=settings.REFRESH_COOKIE_SAMESITE,
        path=settings.REFRESH_COOKIE_PATH,
        domain=settings.REFRESH_COOKIE_DOMAIN,
    )


def clear_refresh_cookie(response):
    response.delete_cookie(
        settings.REFRESH_COOKIE_NAME,
        path=settings.REFRESH_COOKIE_PATH,
        domain=settings.REFRESH_COOKIE_DOMAIN,
        samesite=settings.REFRESH_COOKIE_SAMESITE,
    )


def token_response(user, message):
    access, refresh = tokens.issue_tokens(user)
    response = api_success({"access_token": access, "user": MeSerializer(user).data}, message)
    set_refresh_cookie(response, refresh)
    return response


class PublicAuthView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"


class RegisterView(PublicAuthView):
    """UC-01: Đăng ký -> tạo user email_verified=False -> gửi OTP kích hoạt qua email."""

    @extend_schema(request=RegisterSerializer)
    def post(self, request):
        s = RegisterSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        user = services.register(**s.validated_data)
        return api_success(
            {"email": user.email, "otp_ttl": settings.OTP_TTL_SECONDS},
            "Đăng ký thành công! Mã kích hoạt đã được gửi tới email của bạn.",
            status.HTTP_201_CREATED,
        )


class VerifyEmailView(PublicAuthView):
    """UC-01: Nhập OTP -> kích hoạt tài khoản -> cấp ngay cặp token."""

    @extend_schema(request=OtpVerifySerializer)
    def post(self, request):
        s = OtpVerifySerializer(data=request.data)
        s.is_valid(raise_exception=True)
        user = services.verify_email(s.validated_data["email"], s.validated_data["otp"])
        return token_response(user, "Kích hoạt tài khoản thành công!")


class RequestOtpView(PublicAuthView):
    """Gửi (lại) OTP cho: register | login | reset. Chống spam 60 giây/lần."""

    throttle_scope = "otp"

    @extend_schema(request=OtpRequestSerializer)
    def post(self, request):
        s = OtpRequestSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        services.request_otp(s.validated_data["email"], s.validated_data["purpose"])
        return api_success(
            {"otp_ttl": settings.OTP_TTL_SECONDS, "cooldown": settings.OTP_RESEND_COOLDOWN_SECONDS},
            "Nếu email hợp lệ, mã OTP đã được gửi. Mã có hiệu lực 5 phút.",
        )


class LoginView(PublicAuthView):
    """UC-02: Đăng nhập bằng mật khẩu. Sai 5 lần -> khóa 15 phút (HTTP 429)."""

    @extend_schema(request=LoginSerializer)
    def post(self, request):
        s = LoginSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        user = services.login_with_password(s.validated_data["email"], s.validated_data["password"], client_ip(request))
        return token_response(user, "Đăng nhập thành công!")


class OtpLoginView(PublicAuthView):
    """UC-03: Đăng nhập không mật khẩu bằng OTP gửi qua email."""

    @extend_schema(request=OtpVerifySerializer)
    def post(self, request):
        s = OtpVerifySerializer(data=request.data)
        s.is_valid(raise_exception=True)
        user = services.login_with_otp(s.validated_data["email"], s.validated_data["otp"])
        return token_response(user, "Đăng nhập thành công!")


class RefreshView(PublicAuthView):
    """UC-04: Đọc refresh token từ HttpOnly Cookie -> xoay vòng -> cặp token mới."""

    throttle_classes = []

    @extend_schema(request=None)
    def post(self, request):
        raw = request.COOKIES.get(settings.REFRESH_COOKIE_NAME)
        if not raw:
            return api_error("Chưa đăng nhập", status_code=status.HTTP_401_UNAUTHORIZED, code="NO_REFRESH")
        try:
            uid = tokens.rotate_refresh(raw)
            user = services.get_active_user(uid)
        except ServiceError as exc:
            response = api_error(exc.message, status_code=status.HTTP_401_UNAUTHORIZED, code=exc.code)
            clear_refresh_cookie(response)
            return response
        return token_response(user, "Làm mới phiên thành công")


class LogoutView(APIView):
    """UC-05: Thu hồi refresh token, đưa access token vào blacklist Redis, xóa cookie."""

    permission_classes = [AllowAny]

    @extend_schema(request=None)
    def post(self, request):
        raw = request.COOKIES.get(settings.REFRESH_COOKIE_NAME)
        if raw:
            tokens.revoke_refresh(raw)
        header = request.headers.get("Authorization", "")
        if header.startswith("Bearer "):
            tokens.blacklist_access(header.split(" ", 1)[1])
        response = api_success(message="Đã đăng xuất")
        clear_refresh_cookie(response)
        return response


class ForgotPasswordView(PublicAuthView):
    """UC-06: Yêu cầu OTP đặt lại mật khẩu."""

    throttle_scope = "otp"

    @extend_schema(request=EmailSerializer)
    def post(self, request):
        s = EmailSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        services.request_otp(s.validated_data["email"], "reset")
        return api_success({"otp_ttl": settings.OTP_TTL_SECONDS}, "Nếu email tồn tại, mã đặt lại mật khẩu đã được gửi.")


class ResetPasswordView(PublicAuthView):
    """UC-06: Nhập OTP + mật khẩu mới. Mọi phiên cũ bị thu hồi."""

    @extend_schema(request=ResetPasswordSerializer)
    def post(self, request):
        s = ResetPasswordSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        services.reset_password(s.validated_data["email"], s.validated_data["otp"], s.validated_data["new_password"])
        return api_success(message="Đặt lại mật khẩu thành công, hãy đăng nhập bằng mật khẩu mới.")


class ChangePasswordView(APIView):
    """UC-06: Đổi mật khẩu khi đang đăng nhập -> thu hồi phiên khác, cấp token mới cho phiên này."""

    @extend_schema(request=ChangePasswordSerializer)
    def post(self, request):
        s = ChangePasswordSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        user = services.change_password(
            request.user, s.validated_data["old_password"], s.validated_data["new_password"]
        )
        return token_response(user, "Đổi mật khẩu thành công")


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return api_success(MeSerializer(request.user).data)
