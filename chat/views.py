from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.renders import UserRenderer
from chat.constants import DEFAULT_MAX_QUESTIONS, SESSION_ACTIVE
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

        intake_data = {
            "user_choice": session.intake_data.user_choice,
            "intake_data": session.intake_data.intake_data,
        }

        # Auto-generate title from first question if not set
        if not session.title:
            session.set_title_from_question(question)

        chat_history = session.get_chat_history()

        if not session.can_accept_question():
            return Response(
                {
                    "message": f"You've reached the maximum of {DEFAULT_MAX_QUESTIONS} questions per session. Please start a new chat to continue.",
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
            mcq_message = ChatMessage.objects.select_related("session").get(
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
        chat_history = session.get_chat_history()

        chat_service = ChatService(session)

        try:
            response_data = chat_service.process_mcq_response(
                mcq_message_id,
                selected_value,
                intake_data,
                chat_history,
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
        sessions = ChatSession.objects.filter(user=request.user).prefetch_related(
            "messages"
        )

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
