from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from accounts.views import (
    EmailLoginAPIView,
    ForgetPasswordRequestAPIView,
    ResetPasswordAPIView,
    SignupAPIView,
    UserDetailAPIView,
    VerifyOTPAPIView,
)

urlpatterns = [
    path("signup/", SignupAPIView.as_view(), name="signup"),
    path("login/", EmailLoginAPIView.as_view(), name="email_login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path(
        "forgot-password/",
        ForgetPasswordRequestAPIView.as_view(),
        name="forgot_password",
    ),
    path("verify-otp/", VerifyOTPAPIView.as_view(), name="verify_otp"),
    path("reset-password/", ResetPasswordAPIView.as_view(), name="reset_password"),
    path("user/profile/", UserDetailAPIView.as_view(), name="user-detail"),
]
