from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.contrib.auth.views import LogoutView

from users.views import (
    # 🌐 Template Views
    home_view,
    register_view,
    CustomLoginView,
    request_password_reset,
    recover_password,
    resend_password_otp,

    # 🔌 API Views
    register_user,
    user_profile,
    resend_otp,
    verify_phone,
    request_password_reset_api,
    recover_password_api
)

app_name = "users"

urlpatterns = [
    # 🔐 JWT Authentication
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # 👤 Authenticated User Profile
    path("api/me/", user_profile, name="user-profile"),

    # 📝 Registration & OTP APIs
    path("api/register/", register_user, name="user-register"),
    path("api/resend-otp/", resend_otp, name="resend-otp"),
    path("api/verify-phone/", verify_phone, name="verify-phone"),

    # 🔑 Password Recovery APIs
    path("api/request-password-otp/", request_password_reset_api, name="request-password-otp-api"),
    path("api/recover-password/", recover_password_api, name="recover-password-api"),

    # 🌐 Template-Based Views
    path("", home_view, name="home"),  # 🏠 Home page
    path("signup/", register_view, name="register"),  # 📝 Register page
    path("login-page/", CustomLoginView.as_view(), name="login"),  # 🔐 Login page
    path("logout/", LogoutView.as_view(next_page="users:home"), name="logout"),  # 🚪 Logout
    path("request-password-otp/", request_password_reset, name="template-request-password-otp"),
    path("recover-password/", recover_password, name="template-recover-password"),
    path("resend-password-otp/", resend_password_otp, name="template-resend-password-otp"),
]