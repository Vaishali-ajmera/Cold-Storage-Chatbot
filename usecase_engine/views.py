import os
import random
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from rest_framework import status

from usecase_engine.models import UserInput
from usecase_engine.serializers import (
    UserInputReadSerializer,
    UserInputWriteSerializer,
)
from accounts.renders import UserRenderer
from usecase_engine.constants import SUGGESTED_QUESTIONS_DATA, TYPE_BUILD, TYPE_EXISTING, SYSTEM_PROMPT



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
                    "message": "User inputs retrieved successfully"
                },
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def post(self, request):
        user_choice = request.data.get("user_choice")
        intake_data = request.data.get("intake_data")

        if not user_choice:
            return Response(
                {"error": "user_choice field is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if intake_data is None:
            return Response(
                {"error": "intake_data field is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            serializer = UserInputWriteSerializer(
                data={
                    "user_choice": user_choice,
                    "intake_data": intake_data,
                },
                context={"request": request}
            )
            if serializer.is_valid():
                serializer.save()
                return Response(
                    {
                        "data": serializer.data,
                        "message": "Intake created successfully"
                    },
                    status=status.HTTP_201_CREATED
                )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
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
                    {"error": "Intake not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            serializer = UserInputReadSerializer(intake)
            return Response(
                {
                    "data": serializer.data,
                    "message": "Intake retrieved successfully"
                },
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def patch(self, request, pk):
        try:
            intake = self.get_object(pk, request.user)
            if not intake:
                return Response(
                    {"error": "Intake not found"},
                    status=status.HTTP_404_NOT_FOUND
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
                    {
                        "data": serializer.data,
                        "message": "Intake updated successfully"
                    },
                    status=status.HTTP_200_OK
                )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def delete(self, request, pk):
        try:
            intake = self.get_object(pk, request.user)
            if not intake:
                return Response(
                    {"error": "Intake not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            intake.delete()
            return Response(
                {"message": "Intake deleted successfully"},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )




class SuggestedRelatedAPIView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_type = request.query_params.get('type')

        if user_type not in SUGGESTED_QUESTIONS_DATA:
            return Response(
                {"error": f"Invalid type. Use '{TYPE_BUILD}' or '{TYPE_EXISTING}'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        data = SUGGESTED_QUESTIONS_DATA[user_type]
        
        random_questions = random.sample(data["questions"], 3)

        return Response({
            "message": "Suggested questions retrieved successfully",
            "data": {
                "user_type": user_type,
                "label": data["label"],
                "suggested_questions": random_questions
            }
        }, status=status.HTTP_200_OK)
    

