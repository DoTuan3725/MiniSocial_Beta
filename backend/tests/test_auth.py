"""UC-01 -> UC-06: đăng ký OTP, đăng nhập mật khẩu / OTP, refresh rotation, đăng xuất, mật khẩu."""

from unittest import mock

import pytest
from django.contrib.auth import get_user_model

from apps.authentication import otp

from .factories import UserFactory

pytestmark = pytest.mark.django_db
PASSWORD = "Matkhau@123"


def _otp_sent(mocked):
    """Lấy mã OTP từ lần gọi send_otp_email gần nhất."""
    return mocked.call_args[0][1]


@pytest.fixture
def mail():
    with mock.patch("apps.authentication.services.send_otp_email.delay") as m:
        yield m


def test_register_then_verify_issues_tokens(api, mail):
    r = api.post(
        "/api/v1/auth/register/",
        {"email": "Moi@Test.vn", "password": PASSWORD, "full_name": "Người Mới", "birth_date": "2004-05-01"},
        format="json",
    )
    assert r.status_code == 201, r.data
    user = get_user_model().objects.get(email="moi@test.vn")
    assert not user.email_verified
    assert user.profile.birth_date.isoformat() == "2004-05-01"  # listener của phân hệ User tạo profile

    # chưa kích hoạt thì không đăng nhập được
    r = api.post("/api/v1/auth/login/", {"email": "moi@test.vn", "password": PASSWORD}, format="json")
    assert r.status_code == 403 and r.data["code"] == "EMAIL_NOT_VERIFIED"

    code = _otp_sent(mail)
    r = api.post("/api/v1/auth/verify-email/", {"email": "moi@test.vn", "otp": code}, format="json")
    assert r.status_code == 200
    assert r.data["data"]["access_token"]
    assert "refresh_token" in r.cookies and r.cookies["refresh_token"]["httponly"]


def test_register_rejects_weak_password_and_duplicate(api, mail, user):
    r = api.post(
        "/api/v1/auth/register/", {"email": "x@test.vn", "password": "abcdefgh", "full_name": "X"}, format="json"
    )
    assert r.status_code == 400
    r = api.post("/api/v1/auth/register/", {"email": user.email, "password": PASSWORD, "full_name": "X"}, format="json")
    assert r.status_code == 400 and r.data["code"] == "EMAIL_EXISTS"


def test_otp_wrong_attempts_and_cooldown(api, mail):
    api.post("/api/v1/auth/register/", {"email": "a@test.vn", "password": PASSWORD, "full_name": "A"}, format="json")
    for _ in range(4):
        r = api.post("/api/v1/auth/verify-email/", {"email": "a@test.vn", "otp": "000000"}, format="json")
        assert r.data["code"] in ("OTP_INVALID",)
    r = api.post("/api/v1/auth/verify-email/", {"email": "a@test.vn", "otp": "000000"}, format="json")
    assert r.data["code"] == "OTP_LOCKED"
    # gửi lại ngay lập tức bị chặn bởi cooldown 60s
    r = api.post("/api/v1/auth/otp/request/", {"email": "a@test.vn", "purpose": "register"}, format="json")
    assert r.status_code == 429


def test_password_login_and_bruteforce_lock(api, user):
    r = api.post("/api/v1/auth/login/", {"email": user.email, "password": PASSWORD}, format="json")
    assert r.status_code == 200
    for _ in range(5):
        r = api.post("/api/v1/auth/login/", {"email": user.email, "password": "Sai@12345"}, format="json")
        assert r.status_code == 401
    r = api.post("/api/v1/auth/login/", {"email": user.email, "password": PASSWORD}, format="json")
    assert r.status_code == 429 and r.data["code"] == "LOGIN_LOCKED"


def test_banned_user_cannot_login(api):
    banned = UserFactory(is_active=False)
    r = api.post("/api/v1/auth/login/", {"email": banned.email, "password": PASSWORD}, format="json")
    assert r.status_code == 403 and r.data["code"] == "ACCOUNT_BANNED"


def test_passwordless_otp_login(api, mail, user):
    r = api.post("/api/v1/auth/otp/request/", {"email": user.email, "purpose": "login"}, format="json")
    assert r.status_code == 200
    r = api.post("/api/v1/auth/login/otp/", {"email": user.email, "otp": _otp_sent(mail)}, format="json")
    assert r.status_code == 200 and r.data["data"]["user"]["email"] == user.email


def test_otp_request_does_not_leak_unknown_email(api, mail):
    r = api.post("/api/v1/auth/otp/request/", {"email": "khongco@test.vn", "purpose": "login"}, format="json")
    assert r.status_code == 200
    mail.assert_not_called()


def test_refresh_rotation_and_reuse_detection(api, user):
    r = api.post("/api/v1/auth/login/", {"email": user.email, "password": PASSWORD}, format="json")
    first_refresh = r.cookies["refresh_token"].value
    r = api.post("/api/v1/auth/refresh/")
    assert r.status_code == 200
    second_refresh = r.cookies["refresh_token"].value
    assert second_refresh != first_refresh

    # Kẻ gian dùng lại refresh token cũ -> bị phát hiện, toàn bộ phiên bị thu hồi
    api.cookies["refresh_token"] = first_refresh
    r = api.post("/api/v1/auth/refresh/")
    assert r.status_code == 401 and r.data["code"] == "REFRESH_REUSED"
    api.cookies["refresh_token"] = second_refresh
    assert api.post("/api/v1/auth/refresh/").status_code == 401


def test_logout_blacklists_access_token(api, user):
    r = api.post("/api/v1/auth/login/", {"email": user.email, "password": PASSWORD}, format="json")
    access = r.data["data"]["access_token"]
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
    assert api.get("/api/v1/auth/me/").status_code == 200
    assert api.post("/api/v1/auth/logout/").status_code == 200
    assert api.get("/api/v1/auth/me/").status_code == 401
    assert api.post("/api/v1/auth/refresh/").status_code == 401


def test_forgot_and_reset_password(api, mail, user):
    api.post("/api/v1/auth/password/forgot/", {"email": user.email}, format="json")
    code = _otp_sent(mail)
    r = api.post(
        "/api/v1/auth/password/reset/", {"email": user.email, "otp": code, "new_password": "MoiMoi@456"}, format="json"
    )
    assert r.status_code == 200
    r = api.post("/api/v1/auth/login/", {"email": user.email, "password": "MoiMoi@456"}, format="json")
    assert r.status_code == 200


def test_change_password_revokes_old_sessions(client_a, user):
    old = client_a._credentials["HTTP_AUTHORIZATION"]
    r = client_a.post(
        "/api/v1/auth/password/change/", {"old_password": PASSWORD, "new_password": "Doi@MatKhau9"}, format="json"
    )
    assert r.status_code == 200
    client_a.credentials(HTTP_AUTHORIZATION=old)
    assert client_a.get("/api/v1/auth/me/").status_code == 401


def test_otp_module_direct():
    code = otp.create_otp("login", "z@test.vn")
    assert len(code) == 6
    assert otp.verify_otp("login", "z@test.vn", code)


def test_resend_email_task_mock_mode():
    from apps.authentication.tasks import send_otp_email

    assert send_otp_email.apply(args=["a@test.vn", "123456", "register"]).get() is True


def test_resend_email_real_call(settings):
    from apps.authentication.emails import send_email

    settings.RESEND_API_KEY = "re_test"
    with mock.patch("apps.authentication.emails.requests.post") as post:
        post.return_value.json.return_value = {"id": "x"}
        assert send_email("a@test.vn", "s", "<p>h</p>") == {"id": "x"}
        assert post.call_args.kwargs["headers"]["Authorization"] == "Bearer re_test"


def test_health(api):
    r = api.get("/api/health/")
    assert r.status_code == 200 and r.json()["checks"]["redis"] == "ok"
