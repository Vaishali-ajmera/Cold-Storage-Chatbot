import json
import os
import random

from decouple import config
from google import genai
from google.genai import types
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.renders import UserRenderer
from chat.constants import (
    MESSAGE_TYPE_BOT_ANSWER,
    SENDER_BOT,
    SESSION_ACTIVE,
    WELCOME_MESSAGE_BUILD,
    WELCOME_MESSAGE_DEFAULT,
    WELCOME_MESSAGE_EXISTING,
)
from chat.models import ChatMessage, ChatSession
from usecase_engine.constants import (
    MODEL_NAME,
    SUGGESTED_QUESTIONS_SYSTEM_PROMPT,
    TYPE_BUILD,
    TYPE_EXISTING,
)
from usecase_engine.models import UserInput
from usecase_engine.serializers import UserInputWriteSerializer


class UserInputAPIView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user_choice = request.data.get("user_choice")
        intake_data = request.data.get("intake_data")
        is_active = request.data.get("is_active", True)

        if not user_choice:
            return Response(
                {"error": "user_choice field is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if intake_data is None:
            return Response(
                {"error": "intake_data field is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            if is_active:
                UserInput.objects.filter(user=request.user, is_active=True).update(
                    is_active=False
                )

            serializer = UserInputWriteSerializer(
                data={
                    "user_choice": user_choice,
                    "intake_data": intake_data,
                    "is_active": is_active,
                },
                context={"request": request},
            )

            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            user_input_instance = serializer.save()

            chat_session = ChatSession.objects.create(
                user=request.user,
                intake_data=user_input_instance,
                status=SESSION_ACTIVE,
            )

            # Determine base welcome message
            if user_choice == TYPE_BUILD:
                original_welcome = WELCOME_MESSAGE_BUILD
            elif user_choice == TYPE_EXISTING:
                original_welcome = WELCOME_MESSAGE_EXISTING
            else:
                original_welcome = WELCOME_MESSAGE_DEFAULT

            user_language = request.user.preferred_language

            from usecase_engine.utils import generate_localized_onboarding_content

            welcome_message, suggested_questions = (
                generate_localized_onboarding_content(
                    user_choice, intake_data, user_language, original_welcome
                )
            )

            user_input_instance.suggestions = suggested_questions
            user_input_instance.welcome_message = welcome_message
            user_input_instance.save(update_fields=["suggestions", "welcome_message"])

            welcome_chat_message = ChatMessage.objects.create(
                session=chat_session,
                sender=SENDER_BOT,
                message_text=welcome_message,
                message_type=MESSAGE_TYPE_BOT_ANSWER,
                suggested_questions=suggested_questions,
            )

            return Response(
                {
                    "message": "Intake created and suggestions generated successfully",
                    "data": {
                        "intake": serializer.data,
                        "session_id": str(chat_session.id),
                        "suggested_questions": suggested_questions,
                        "welcome_message": welcome_message,
                    },
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
