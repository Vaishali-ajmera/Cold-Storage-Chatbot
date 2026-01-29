# authentication/views.py
import logging
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.hashers import make_password
from django.utils import timezone

User = get_user_model()
from django.utils.crypto import get_random_string
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.constants import DEFAULT_LANGUAGE
from accounts.models import UserOTP
from accounts.renders import UserRenderer
from accounts.serializers import UserSerializer
from accounts.tasks import (
    send_forgot_password_email_task,
    send_password_reset_success_email_task,
    send_welcome_email_task,
)


def generate_otp():
    return get_random_string(length=6, allowed_chars="0123456789")


def get_user_data(user):
    """
    Helper function to return standardized user data for login/signup responses.
    """
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "preferred_language": user.preferred_language,
        "has_set_preferences": user.has_set_preferences,
    }


class SignupAPIView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]
            first_name = serializer.validated_data.get("first_name")
            last_name = serializer.validated_data.get("last_name", "")
            password = serializer.validated_data["password"]

            if User.objects.filter(email=email).exists():
                return Response(
                    {"message": "This email is already registered."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            base_username = email.split("@")[0]
            username = base_username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1

            user = User.objects.create(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                is_active=True,
                preferred_language=request.data.get(
                    "preferred_language", DEFAULT_LANGUAGE
                ),
            )
            if "preferred_language" in request.data:
                user.has_set_preferences = True

            user.set_password(password)
            user.save()

            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)

            full_name = f"{first_name} {last_name}".strip()
            try:
                send_welcome_email_task.delay(email, full_name)
            except Exception as e:
                print(f"Error queuing welcome email: {str(e)}")

            return Response(
                {
                    "message": "User registered successfully",
                    "data": {
                        "refresh": refresh_token,
                        "access": access_token,
                        "user": get_user_data(user),
                    },
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {"message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
        )


class EmailLoginAPIView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response(
                {"error": "Email and password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(request, email=email, password=password)

        if not user:
            return Response(
                {"error": "Invalid email or password."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        user.last_login = timezone.now()
        user.save(update_fields=["last_login"])

        return Response(
            {
                "message": "Login successful",
                "data": {
                    "refresh": refresh_token,
                    "access": access_token,
                    "user": get_user_data(user),
                },
            },
            status=status.HTTP_200_OK,
        )


class ForgetPasswordRequestAPIView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"error": "Email is required."}, status=400)

        try:
            user = User.objects.get(email=email)

            # Check recent OTP to prevent spam
            recent_otp = (
                UserOTP.objects.filter(user=user, purpose="forgot_password")
                .order_by("-otp_created_at")
                .first()
            )

            if recent_otp:
                resend_threshold = recent_otp.otp_created_at + timedelta(
                    minutes=getattr(settings, "OTP_RESEND_LIMIT_MINUTES", 2)
                )
                if timezone.now() < resend_threshold:
                    wait_time = (
                        int((resend_threshold - timezone.now()).total_seconds() // 60)
                        + 1
                    )
                    return Response(
                        {
                            "message": f"Please wait {wait_time} minute(s) before requesting a new OTP."
                        },
                        status=429,  # Too Many Requests
                    )

            # Generate and save OTP
            otp = generate_otp()
            UserOTP.objects.update_or_create(
                user=user,
                purpose="forgot_password",
                defaults={"otp_code": otp, "otp_created_at": timezone.now()},
            )

            # Send OTP email using Celery task
            send_forgot_password_email_task.delay(
                user.email,
                user.get_full_name() or user.email.split("@")[0],
                otp,
                getattr(settings, "OTP_EXPIRY_MINUTES", 10),
            )

            return Response({"message": "OTP sent to your email."}, status=200)

        except User.DoesNotExist:
            return Response(
                {"error": "User with this email does not exist."}, status=400
            )


class VerifyOTPAPIView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [AllowAny]
    authentication_classes = []  # Disable authentication for OTP verification

    def post(self, request):
        email = request.data.get("email")
        otp = request.data.get("otp")
        purpose = request.data.get("purpose", "forgot_password")

        if not all([email, otp]):
            return Response({"error": "Email and OTP are required."}, status=400)

        if purpose == "forgot_password":
            try:
                user = User.objects.get(email=email)
                user_otp = UserOTP.objects.filter(user=user, purpose=purpose).latest(
                    "otp_created_at"
                )

                if user_otp.otp_code != otp:
                    return Response({"error": "Incorrect OTP"}, status=400)

                if user_otp.is_expired():
                    return Response({"error": "OTP expired"}, status=400)

                return Response(
                    {
                        "message": "OTP verified. You can now reset your password.",
                        "email": user.email,
                    },
                    status=200,
                )

            except (User.DoesNotExist, UserOTP.DoesNotExist):
                return Response({"error": "Invalid email or OTP"}, status=400)
        else:
            return Response({"error": "Invalid OTP purpose."}, status=400)


class ResetPasswordAPIView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [AllowAny]
    authentication_classes = []  # Disable authentication for password reset

    def post(self, request):
        email = request.data.get("email")
        otp = request.data.get("otp")
        new_password = request.data.get("new_password")

        if not all([email, otp, new_password]):
            return Response(
                {"error": "Email, OTP, and new password are required."}, status=400
            )

        try:
            user = User.objects.get(email=email)
            user_otp = UserOTP.objects.filter(
                user=user, purpose="forgot_password"
            ).latest("otp_created_at")
        except (User.DoesNotExist, UserOTP.DoesNotExist):
            return Response({"error": "Invalid email or OTP"}, status=400)

        if user_otp.otp_code != otp:
            return Response({"error": "Incorrect OTP"}, status=400)

        if user_otp.is_expired():
            return Response({"error": "OTP expired"}, status=400)

        user.set_password(new_password)
        user.save()
        user_otp.delete()  # Delete OTP after successful password reset

        try:
            send_password_reset_success_email_task.delay(
                user.email, user.get_full_name() or user.email.split("@")[0]
            )
        except Exception as e:
            print(f"Error queuing password reset success email: {str(e)}")

        return Response({"message": "Password reset successful."}, status=200)


class UserDetailAPIView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            serializer = UserSerializer(user)
            return Response(
                {
                    "message": "User retrieved successfully",
                    "data": serializer.data,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"error": f"Failed to retrieve user: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def post(self, request):
        try:
            user = request.user
            data = request.data

            old_language = user.preferred_language

            if "email" in data:
                user.email = data["email"]

            if "first_name" in data:
                user.first_name = data["first_name"]

            if "last_name" in data:
                user.last_name = data["last_name"]

            if "preferred_language" in data:
                user.preferred_language = data["preferred_language"]
                user.has_set_preferences = True

            user.save()

            if "preferred_language" in data and data["preferred_language"] != old_language:
                from usecase_engine.models import UserInput
                from usecase_engine.utils import generate_localized_onboarding_content
                from usecase_engine.constants import (
                    TYPE_BUILD,
                    TYPE_EXISTING,
                    WELCOME_MESSAGE_BUILD,
                    WELCOME_MESSAGE_EXISTING,
                )

                active_intake = UserInput.objects.filter(
                    user=user, is_active=True
                ).first()

                if active_intake:
                    if active_intake.user_choice == TYPE_BUILD:
                        original_welcome = WELCOME_MESSAGE_BUILD
                    elif active_intake.user_choice == TYPE_EXISTING:
                        original_welcome = WELCOME_MESSAGE_EXISTING
                    else:
                        original_welcome = "Welcome! How can I help you today?"

                    welcome_message, suggestions = generate_localized_onboarding_content(
                        active_intake.user_choice,
                        active_intake.intake_data,
                        user.preferred_language,
                        original_welcome,
                    )

                    active_intake.welcome_message = welcome_message
                    active_intake.suggestions = suggestions
                    active_intake.save(update_fields=["welcome_message", "suggestions"])

            serializer = UserSerializer(user)
            return Response(
                {
                    "message": "User updated successfully",
                    "data": serializer.data,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"error": f"Failed to update user: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
