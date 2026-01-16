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
from usecase_engine.constants import (
    SUGGESTED_QUESTIONS_SYSTEM_PROMPT,
)
from usecase_engine.models import UserInput
from usecase_engine.serializers import UserInputWriteSerializer
from usecase_engine.utils import get_suggested_questions_user_prompt


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

            # Create a new ChatSession for this intake
            from chat.models import ChatSession, ChatMessage
            from chat.constants import (
                SESSION_ACTIVE,
                SENDER_BOT,
                MESSAGE_TYPE_BOT_ANSWER,
                WELCOME_MESSAGE_BUILD,
                WELCOME_MESSAGE_EXISTING,
                WELCOME_MESSAGE_DEFAULT,
            )
            from usecase_engine.constants import TYPE_BUILD, TYPE_EXISTING
            
            chat_session = ChatSession.objects.create(
                user=request.user,
                intake_data=user_input_instance,
                status=SESSION_ACTIVE
            )

            # Determine welcome message based on user_choice
            if user_choice == TYPE_BUILD:
                welcome_message = WELCOME_MESSAGE_BUILD
            elif user_choice == TYPE_EXISTING:
                welcome_message = WELCOME_MESSAGE_EXISTING
            else:
                welcome_message = WELCOME_MESSAGE_DEFAULT

            # Create the welcome message as the first bot message
            welcome_chat_message = ChatMessage.objects.create(
                session=chat_session,
                sender=SENDER_BOT,
                message_text=welcome_message,
                message_type=MESSAGE_TYPE_BOT_ANSWER,
                suggested_questions=None,
            )

            suggested_questions = []
            api_key = config("GEMINI_API_KEY", default=None)

            if api_key:
                try:
                    user_input = get_suggested_questions_user_prompt(
                        user_choice, intake_data
                    )
                    client = genai.Client(api_key=api_key)

                    response = client.models.generate_content(
                        model="gemini-3-flash-preview",
                        config=types.GenerateContentConfig(
                            system_instruction=SUGGESTED_QUESTIONS_SYSTEM_PROMPT,
                            temperature=0.7,
                            response_mime_type="application/json",
                        ),
                        contents=user_input,
                    )

                    raw_reply = json.loads(response.text)
                    suggested_questions = [
                        {"id": idx + 1, "text": q} for idx, q in enumerate(raw_reply)
                    ]
                except Exception as gemini_err:
                    print(f"Gemini generation failed: {gemini_err}")

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
