import json
import os
import random

from decouple import config
from django.shortcuts import get_object_or_404
from google import genai
from google.genai import types
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.renders import UserRenderer
from usecase_engine.constants import (
    SUGGESTED_QUESTIONS_DATA,
    SUGGESTED_QUESTIONS_SYSTEM_PROMPT,
    SUGGESTION_USER_PROMPT,
    SYSTEM_PROMPT,
    TYPE_BUILD,
    TYPE_EXISTING,
)
from usecase_engine.models import UserInput
from usecase_engine.serializers import UserInputReadSerializer, UserInputWriteSerializer
from usecase_engine.utils import get_suggested_questions_user_prompt


class UserInputAPIView(APIView):
    """
    Handles:
    - GET: list all user inputs
    - POST: create a new user input
    """

    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            queryset = UserInput.objects.filter(user=request.user)
            serializer = UserInputReadSerializer(queryset, many=True)
            return Response(
                {
                    "data": serializer.data,
                    "message": "User inputs retrieved successfully",
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def post(self, request):
        user_choice = request.data.get("user_choice")
        intake_data = request.data.get("intake_data")
        is_active = request.data.get("is_active", True)  # Default to True

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
            # If creating an active input, deactivate all existing inputs for this user
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

            serializer.save()

            # --- Gemini Integration for Suggested Questions ---
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
                        "suggested_questions": suggested_questions,
                    },
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
