# chat/views.py

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.renders import UserRenderer
from chat.constants import SESSION_ACTIVE
from chat.models import ChatMessage, ChatSession
from chat.serializers import (
    ChatHistorySerializer,
    ChatSessionSerializer,
    UserMCQResponseSerializer,
    UserQuestionInputSerializer,
)
from chat.services import ChatService


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
                user=request.user, intake_data=active_intake, status=SESSION_ACTIVE
            )

        # Prepare intake data (raw from DB)
        intake_data = {
            "user_choice": session.intake_data.user_choice,
            "intake_data": session.intake_data.intake_data
        }
        
        # Prepare chat history
        chat_history = session.get_chat_history()

        if not session.can_accept_question():
            return Response(
                {
                    "message": "Question limit reached for this session. Please start a new chat.",
                    "data": {
                        "session_id": str(session.id),
                        "user_questions_count": session.user_questions_count,
                        "remaining_questions": session.remaining_questions(),
                        "status": session.status,
                        "limit_reached": True,
                        "history": ChatHistorySerializer(session.messages.all().order_by("sequence_number"), many=True).data,
                    },
                },
                status=status.HTTP_200_OK,
            )

        chat_service = ChatService(session)

        try:
            response_data = chat_service.process_user_question(
                question, intake_data, chat_history
            )
        except Exception as e:
            return Response(
                {"error": "Failed to process question"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {
                "message": "Question processed successfully",
                "data": {
                    "session_id": str(session.id),
                    "history": chat_history,
                    "type": response_data.get("type"),
                    "response_message": response_data.get("message"),
                    "suggestions": response_data.get("suggestions"),
                    "mcq": response_data.get("mcq"),
                    "mcq_message_id": response_data.get("mcq_message_id"),
                    "remaining_questions": response_data.get("remaining_questions"),
                },
            },
            status=status.HTTP_200_OK,
        )


class AnswerMCQView(APIView):
    """
    POST /api/chat/mcq-response/

    User responds to MCQ question
    """

    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Validate input
        serializer = UserMCQResponseSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
            )

        mcq_message_id = serializer.validated_data["mcq_message_id"]
        selected_option = serializer.validated_data["selected_option"]
        selected_value = serializer.validated_data["selected_value"]

        # Get message and session
        try:
            mcq_message = ChatMessage.objects.select_related("session").get(
                id=mcq_message_id
            )
            session = mcq_message.session

            # Verify session belongs to user
            if session.user != request.user:
                return Response(
                    {"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN
                )

        except ChatMessage.DoesNotExist:
            return Response(
                {"error": "MCQ message not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Prepare intake data and chat history
        intake_data = {
            "user_choice": session.intake_data.user_choice,
            "intake_data": session.intake_data.intake_data
        }
        chat_history = session.get_chat_history()
        
        # Process MCQ response
        chat_service = ChatService(session)

        try:
            response_data = chat_service.process_mcq_response(
                mcq_message_id, selected_option, selected_value,
                intake_data, chat_history
            )

            return Response(
                {
                    "message": "MCQ response processed successfully",
                    "data": {"session_id": str(session.id), **response_data},
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"error": f"Failed to process MCQ response: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ChatHistoryView(APIView):
    """
    GET /api/chat/history/<session_id>/

    Get full chat history for a session
    """

    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request, session_id):
        try:
            session = ChatSession.objects.get(id=session_id, user=request.user)
        except ChatSession.DoesNotExist:
            return Response(
                {"error": "Session not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Get all messages
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
    """
    GET: List all chat sessions for a user (for chat history sidebar)
    """

    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        List user's sessions

        Response:
        {
            "sessions": [
                {
                    "id": "uuid",
                    "started_at": "2024-12-24T10:00:00Z",
                    "status": "active",
                    "user_questions_count": 2,
                    "last_message_preview": "For chips-grade potatoes..."
                },
                {
                    "id": "uuid",
                    "started_at": "2024-12-23T15:00:00Z",
                    "status": "limit_reached",
                    "user_questions_count": 4,
                    "last_message_preview": "Solar panels can reduce..."
                },
                ...
            ]
        }
        """
        # TODO: Implement session listing
        pass
