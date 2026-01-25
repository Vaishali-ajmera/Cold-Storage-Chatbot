import logging

from celery.result import AsyncResult
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.renders import UserRenderer
from advisory.celery import app as celery_app
from chat.constants import SESSION_ACTIVE
from chat.models import ChatMessage, ChatSession
from chat.serializers import (
    ChatHistorySerializer,
    ChatSessionSerializer,
    SessionListSerializer,
    UpdateSessionTitleSerializer,
    UserMCQResponseSerializer,
    UserQuestionInputSerializer,
)
from chat.services import ChatService
from chat.tasks import process_mcq_response_task, process_question_task

logger = logging.getLogger("chat.views")


class AskQuestionView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = UserQuestionInputSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        question = serializer.validated_data["question"]
        session = serializer.validated_data.get("session_id")

        from chat.models import DailyQuestionQuota
        from chat.constants import DEFAULT_MAX_DAILY_QUESTIONS
        
        daily_quota = DailyQuestionQuota.get_or_create_today(request.user)
        
        if not daily_quota.can_ask_question():
            return Response(
                {
                    "message": f"You've reached your daily limit of {DEFAULT_MAX_DAILY_QUESTIONS} questions. Please try again tomorrow.",
                    "data": {
                        "error_code": "DAILY_QUOTA_EXCEEDED",
                        "remaining_daily_questions": 0,
                    }
                },
                status=status.HTTP_200_OK,
            )

        if not session:
            from usecase_engine.models import UserInput

            active_intake = UserInput.objects.filter(
                user=request.user, is_active=True
            ).first()

            if not active_intake:
                return Response(
                    {
                        "error": "No active intake data found. Please complete intake first."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            session = ChatSession.objects.create(
                user=request.user, intake_data=active_intake
            )

        intake_data = {
            "user_choice": session.intake_data.user_choice,
            "intake_data": session.intake_data.intake_data,
        }

        if not session.title:
            session.set_title_from_question(question)

        daily_quota.increment_count()

        task = process_question_task.delay(
            session_id=str(session.id),
            question=question,
            intake_data=intake_data,
            user_id=request.user.id,
        )

        logger.info(f"Queued question task {task.id} for session {session.id}")

        return Response(
            {
                "message": "Question submitted for processing",
                "data": {
                    "task_id": task.id,
                    "session_id": str(session.id),
                    "status": "PENDING",
                    "remaining_daily_questions": daily_quota.remaining_questions(),
                },
            },
            status=status.HTTP_202_ACCEPTED,
        )


class AnswerMCQView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = UserMCQResponseSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        mcq_message_id = serializer.validated_data["mcq_message_id"]
        selected_value = serializer.validated_data["selected_value"]

        try:
            mcq_message = ChatMessage.objects.select_related("session__intake_data").get(
                id=mcq_message_id
            )
            session = mcq_message.session

            if session.user != request.user:
                return Response(
                    {"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN
                )

        except ChatMessage.DoesNotExist:
            return Response(
                {"error": "MCQ message not found"}, status=status.HTTP_404_NOT_FOUND
            )

        intake_data = {
            "user_choice": session.intake_data.user_choice,
            "intake_data": session.intake_data.intake_data,
        }

        task = process_mcq_response_task.delay(
            session_id=str(session.id),
            mcq_message_id=str(mcq_message_id),
            selected_value=selected_value,
            intake_data=intake_data,
            user_id=request.user.id,
        )

        logger.info(f"Queued MCQ task {task.id} for session {session.id}")

        return Response(
            {
                "message": "MCQ response submitted for processing",
                "data": {
                    "task_id": task.id,
                    "session_id": str(session.id),
                    "status": "PENDING",
                },
            },
            status=status.HTTP_202_ACCEPTED,
        )


class ChatHistoryView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request, session_id):
        try:
            session = ChatSession.objects.get(id=session_id, user=request.user)
        except ChatSession.DoesNotExist:
            return Response(
                {"error": "Session not found"}, status=status.HTTP_404_NOT_FOUND
            )

        messages = session.messages.all().order_by("sequence_number")

        return Response(
            {
                "message": "Chat history retrieved successfully",
                "data": {
                    "session": ChatSessionSerializer(session).data,
                    "messages": ChatHistorySerializer(messages, many=True).data,
                },
            },
            status=status.HTTP_200_OK,
        )


class ListUserSessionsAPIView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        sessions = ChatSession.objects.filter(user=request.user)

        serializer = SessionListSerializer(sessions, many=True)

        return Response(
            {
                "message": "Sessions retrieved successfully",
                "data": {"sessions": serializer.data},
            },
            status=status.HTTP_200_OK,
        )


class UpdateSessionTitleAPIView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated]

    def patch(self, request, session_id):
        try:
            session = ChatSession.objects.get(id=session_id, user=request.user)
        except ChatSession.DoesNotExist:
            return Response(
                {"error": "Session not found"}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = UpdateSessionTitleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        session.title = serializer.validated_data["title"]
        session.save(update_fields=["title"])

        return Response(
            {
                "message": "Session title updated successfully",
                "data": {"id": str(session.id), "title": session.title},
            },
            status=status.HTTP_200_OK,
        )


class GetSessionIntakeView(APIView):

    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request, session_id):
        try:
            session = ChatSession.objects.select_related("intake_data").get(
                id=session_id, user=request.user
            )
        except ChatSession.DoesNotExist:
            return Response(
                {"error": "Chat session not found"}, status=status.HTTP_404_NOT_FOUND
            )

        if not session.intake_data:
            return Response(
                {"error": "No intake data associated with this session"},
                status=status.HTTP_404_NOT_FOUND,
            )

        from usecase_engine.serializers import UserInputReadSerializer

        serializer = UserInputReadSerializer(session.intake_data)

        return Response(
            {
                "message": "Intake data retrieved successfully",
                "data": {
                    "session_id": str(session.id),
                    "intake": serializer.data,
                },
            },
            status=status.HTTP_200_OK,
        )


class CreateSessionView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            from usecase_engine.models import UserInput
            from usecase_engine.constants import TYPE_BUILD, TYPE_EXISTING
            from chat.constants import (
                WELCOME_MESSAGE_BUILD,
                WELCOME_MESSAGE_EXISTING,
                WELCOME_MESSAGE_DEFAULT,
                MESSAGE_TYPE_BOT_ANSWER,
                SENDER_BOT,
            )

            active_intake = UserInput.objects.filter(
                user=request.user, is_active=True
            ).first()

            if not active_intake:
                return Response(
                    {
                        "error": "No active intake data found. Please complete the intake form first."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Create a new chat session with the active intake data
            session = ChatSession.objects.create(
                user=request.user,
                intake_data=active_intake,
                status=SESSION_ACTIVE,
            )
            
            # Ensure intake has pre-generated onboarding content
            if not active_intake.suggestions or not active_intake.welcome_message:
                return Response(
                    {
                        "error": "Session initialization data missing. Please complete the intake form first."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            welcome_message = active_intake.welcome_message
            suggested_questions = active_intake.suggestions

            welcome_chat_message = ChatMessage.objects.create(
                session=session,
                sender=SENDER_BOT,
                message_text=welcome_message,
                message_type=MESSAGE_TYPE_BOT_ANSWER,
                suggested_questions=suggested_questions,
            )

            
            
            from chat.models import DailyQuestionQuota
            daily_quota = DailyQuestionQuota.get_or_create_today(request.user)

            return Response(
                {
                    "message": "New chat session created successfully",
                    "data": {
                        "session_id": str(session.id),
                        "title": session.title or "New Chat",
                        "status": session.status,
                        "intake_id": str(active_intake.id),
                        "user_choice": active_intake.user_choice,
                        "remaining_daily_questions": daily_quota.remaining_questions(),
                        "can_ask_question": daily_quota.can_ask_question(),
                        "created_at": session.created_at.isoformat(),
                        "welcome_message": welcome_message,
                        "suggested_questions": suggested_questions,
                    },
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
           return Response(
                {"error": f"Failed to create session: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class TaskStatusView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request, task_id):
        try:
            result = AsyncResult(task_id, app=celery_app)
            
            if result.successful():
                task_result = result.result
                
                if task_result and task_result.get("success"):
                    return Response(
                        {
                            "message": "Task completed successfully",
                            "data": {
                                "task_id": task_id,
                                "task_status": "SUCCESS",
                                "session_id": task_result.get("session_id"),
                                "type": task_result.get("type"),
                                "response_message": task_result.get("response_message"),
                                "suggestions": task_result.get("suggestions"),
                                "mcq": task_result.get("mcq"),
                                "mcq_message_id": task_result.get("mcq_message_id"),
                                "remaining_daily_questions": task_result.get("remaining_daily_questions"),
                            },
                        },
                        status=status.HTTP_200_OK,
                    )
                else:
                    # Task completed but with error (e.g., quota exceeded)
                    error_code = "DAILY_QUOTA_EXCEEDED" if task_result.get("daily_limit_reached") else "TASK_FAILED"
                    return Response(
                        {
                            "message": task_result.get("error", "Task failed"),
                            "data": {
                                "task_id": task_id,
                                "task_status": "FAILURE",
                                "error_code": error_code,
                            },
                        },
                        status=status.HTTP_200_OK,
                    )

            elif result.failed():
                return Response(
                    {
                        "message": str(result.result) if result.result else "Task failed",
                        "data": {
                            "task_id": task_id,
                            "task_status": "FAILURE",
                            "error_code": "TASK_FAILED",
                        },
                    },
                    status=status.HTTP_200_OK,
                )

            elif result.status == "PENDING":
                return Response(
                    {
                        "message": "Task is waiting in the queue",
                        "data": {"task_id": task_id, "task_status": "PENDING"},
                    },
                    status=status.HTTP_200_OK,
                )

            elif result.status == "STARTED":
                return Response(
                    {
                        "message": "Task is being processed",
                        "data": {"task_id": task_id, "task_status": "STARTED"},
                    },
                    status=status.HTTP_200_OK,
                )

            elif result.status == "RETRY":
                return Response(
                    {
                        "message": "Task is being retried",
                        "data": {"task_id": task_id, "task_status": "RETRY"},
                    },
                    status=status.HTTP_200_OK,
                )

            else:
                return Response(
                    {
                        "message": f"Task status: {result.status}",
                        "data": {"task_id": task_id, "task_status": result.status},
                    },
                    status=status.HTTP_200_OK,
                )

        except Exception as e:
            logger.error(f"Error checking task status: {str(e)}")
            return Response(
                {
                    "message": f"Failed to check task status: {str(e)}",
                    "data": {"error_code": "TASK_STATUS_ERROR"},
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

