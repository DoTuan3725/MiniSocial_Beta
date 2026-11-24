from django.urls import path

from . import views

urlpatterns = [
    path("register/", views.RegisterView.as_view(), name="auth-register"),
    path("verify-email/", views.VerifyEmailView.as_view(), name="auth-verify-email"),
    path("otp/request/", views.RequestOtpView.as_view(), name="auth-otp-request"),
    path("login/", views.LoginView.as_view(), name="auth-login"),
    path("login/otp/", views.OtpLoginView.as_view(), name="auth-login-otp"),
    path("refresh/", views.RefreshView.as_view(), name="auth-refresh"),
    path("logout/", views.LogoutView.as_view(), name="auth-logout"),
    path("password/forgot/", views.ForgotPasswordView.as_view(), name="auth-password-forgot"),
    path("password/reset/", views.ResetPasswordView.as_view(), name="auth-password-reset"),
    path("password/change/", views.ChangePasswordView.as_view(), name="auth-password-change"),
    path("me/", views.MeView.as_view(), name="auth-me"),
]
