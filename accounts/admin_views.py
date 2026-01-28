import logging

from django.db.models import Avg, Sum
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.admin_serializers import (
    AdminStatsSerializer,
    SystemConfigurationChoicesSerializer,
    SystemConfigurationSerializer,
)
from accounts.models import SystemConfiguration, User
from accounts.permissions import IsAdminUser
from accounts.renders import UserRenderer
from chat.models import ChatMessage, ChatSession, DailyQuestionQuota

logger = logging.getLogger(__name__)


class SystemConfigurationAPIView(APIView):

    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        try:
            config = SystemConfiguration.get_config()
            if config:
                serializer = SystemConfigurationSerializer(config)
                return Response(
                    {
                        "message": "Configuration fetched successfully.",
                        "data": serializer.data,
                    },
                    status=status.HTTP_200_OK,
                )
            return Response(
                {
                    "message": "No configuration found.",
                    "data": None,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            logger.error(f"Error fetching config: {str(e)}")
            return Response(
                {"error": "Failed to fetch configuration."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def post(self, request):
        try:
            config = SystemConfiguration.get_config()
            if config:
                serializer = SystemConfigurationSerializer(
                    config, data=request.data, partial=True
                )
            else:
                serializer = SystemConfigurationSerializer(data=request.data)

            if serializer.is_valid():
                serializer.save(updated_by=request.user)
                return Response(
                    {
                        "message": "Configuration saved successfully.",
                        "data": serializer.data,
                    },
                    status=status.HTTP_200_OK,
                )
            return Response(
                {"error": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logger.error(f"Error saving config: {str(e)}")
            return Response(
                {"error": "Failed to save configuration."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ConfigurationChoicesAPIView(APIView):

    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        try:
            serializer = SystemConfigurationChoicesSerializer({})
            return Response(
                {
                    "message": "Choices fetched successfully.",
                    "data": serializer.data,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            logger.error(f"Error fetching choices: {str(e)}")
            return Response(
                {"error": "Failed to fetch configuration choices."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class AdminStatsAPIView(APIView):

    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        try:
            today = timezone.now().date()

            total_users = User.objects.count()
            total_sessions = ChatSession.objects.count()
            total_messages = ChatMessage.objects.count()

            questions_today = (
                DailyQuestionQuota.objects.filter(date=today).aggregate(
                    total=Sum("question_count")
                )["total"]
                or 0
            )

            avg_result = DailyQuestionQuota.objects.aggregate(avg=Avg("question_count"))
            avg_questions_per_user = round(avg_result["avg"] or 0, 2)

            stats = {
                "total_users": total_users,
                "total_sessions": total_sessions,
                "total_messages": total_messages,
                "questions_today": questions_today,
                "avg_questions_per_user": avg_questions_per_user,
            }

            serializer = AdminStatsSerializer(stats)
            return Response(
                {
                    "message": "Stats fetched successfully.",
                    "data": serializer.data,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            logger.error(f"Error fetching stats: {str(e)}")
            return Response(
                {"error": "Failed to fetch admin statistics."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
