import logging
import re

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.renders import UserRenderer
from accounts.utils import get_user_data, phone_to_email

logger = logging.getLogger(__name__)
User = get_user_model()


class SSOVerifyTokenAPIView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        token = request.data.get("token")

        if not token:
            return Response(
                {"error": "Token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            payload = jwt.decode(
                token,
                settings.SSO_SECRET_KEY,
                algorithms=["HS256"],
            )
        except jwt.ExpiredSignatureError:
            return Response(
                {"error": "Token has expired."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        except jwt.InvalidTokenError as e:
            logger.error(f"SSO token validation failed: {str(e)}")
            return Response(
                {"error": f"Invalid token: {str(e)}"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        phone = payload.get("phone")
        first_name = payload.get("first_name", "User")
        last_name = payload.get("last_name", "")
        is_admin = payload.get("is_admin", False)

        if not phone:
            return Response(
                {"error": "Phone number is required in token."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        derived_email = phone_to_email(phone)

        try:
            user = User.objects.get(phone_number=phone)
            is_new_user = False

            if is_admin and not user.is_staff:
                user.is_staff = True
                user.save(update_fields=["is_staff"])

        except User.DoesNotExist:
            base_username = f"{first_name}"
            username = base_username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}_{counter}"
                counter += 1

            user = User.objects.create(
                username=username,
                email=derived_email,
                phone_number=phone,
                first_name=first_name,
                last_name=last_name,
                is_staff=is_admin,
                is_active=True,
                is_sso_user=True,
            )
            is_new_user = True
            logger.info(f"SSO: Created new user {user.email} from phone {phone}")

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        return Response(
            {
                "message": "SSO login successful",
                "data": {
                    "access": access_token,
                    "refresh": refresh_token,
                    "user": get_user_data(user),
                    "is_new_user": is_new_user,
                },
            },
            status=status.HTTP_200_OK,
        )
