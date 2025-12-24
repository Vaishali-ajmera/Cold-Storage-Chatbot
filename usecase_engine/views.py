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
            serializer = UserInputWriteSerializer(
                data={
                    "user_choice": user_choice,
                    "intake_data": intake_data,
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


class UserInputDetailAPIView(APIView):
    """
    Handles:
    - GET: retrieve one input
    - PATCH: update input
    - DELETE: delete input
    """

    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        try:
            return UserInput.objects.get(pk=pk, user=user)
        except UserInput.DoesNotExist:
            return None

    def get(self, request, pk):
        try:
            intake = self.get_object(pk, request.user)
            if not intake:
                return Response(
                    {"error": "Intake not found"}, status=status.HTTP_404_NOT_FOUND
                )
            serializer = UserInputReadSerializer(intake)
            return Response(
                {"data": serializer.data, "message": "Intake retrieved successfully"},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def patch(self, request, pk):
        try:
            intake = self.get_object(pk, request.user)
            if not intake:
                return Response(
                    {"error": "Intake not found"}, status=status.HTTP_404_NOT_FOUND
                )
            serializer = UserInputWriteSerializer(
                intake,
                data=request.data,
                partial=True,
                context={"request": request},
            )
            if serializer.is_valid():
                serializer.save()
                return Response(
                    {"data": serializer.data, "message": "Intake updated successfully"},
                    status=status.HTTP_200_OK,
                )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def delete(self, request, pk):
        try:
            intake = self.get_object(pk, request.user)
            if not intake:
                return Response(
                    {"error": "Intake not found"}, status=status.HTTP_404_NOT_FOUND
                )
            intake.delete()
            return Response(
                {"message": "Intake deleted successfully"}, status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )



class GeminiAdvisoryAPI(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user_query = request.data.get("question")
        last_question_context = request.data.get("last_question_context")  # Add this
        use_dummy = request.data.get("use_dummy", True)

        if not user_query:
            return Response(
                {"error": "Question is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Use dummy responses for testing
        if use_dummy:
            from usecase_engine.utils import get_dummy_response

            dummy_response = get_dummy_response(user_query, last_question_context)

            if dummy_response:
                # Add last_question_context to response if it's MCQ
                response_data = dummy_response.copy()
                if dummy_response["data"]["type"] == "mcq":
                    response_data["last_question_context"] = user_query

                return Response(response_data, status=status.HTTP_200_OK)
            else:
                return Response(
                    {
                        "message": "No dummy response found for this question",
                        "data": {
                            "answer": "This question is not in the test dataset. Please use actual LLM.",
                            "type": "error",
                        },
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

        # Real LLM call (existing code unchanged)
        api_key = config("GEMINI_API_KEY", default=None)

        if not api_key:
            return Response(
                {"error": "Gemini API key not configured"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        client = genai.Client(api_key=api_key)
        model_id = "gemini-2.0-flash-exp"

        try:
            response = client.models.generate_content(
                model=model_id,
                contents=user_query,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=1.0,
                ),
            )

            raw_text = response.text.strip()

            if "out of context" in raw_text.lower():
                return Response(
                    {
                        "message": "Query is out of context",
                        "data": {
                            "answer": "I can only help with questions related to potato cold storage and advisory.",
                            "type": "out_of_context",
                        },
                    },
                    status=status.HTTP_200_OK,
                )

            is_mcq = "A)" in raw_text and "B)" in raw_text

            return Response(
                {
                    "message": "Response generated successfully",
                    "data": {
                        "answer": raw_text,
                        "type": "mcq" if is_mcq else "answer",
                        "model": model_id,
                    },
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"error": f"Gemini API error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
