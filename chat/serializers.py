from django.contrib.auth import get_user_model
User = get_user_model()
from rest_framework import serializers

from chat.constants import SESSION_ACTIVE
from chat.models import ChatMessage, ChatSession, DailyQuestionQuota


class ChatSessionSerializer(serializers.ModelSerializer):
    remaining_daily_questions = serializers.SerializerMethodField()
    can_ask_question = serializers.SerializerMethodField()

    class Meta:
        model = ChatSession
        fields = [
            "id",
            "user",
            "intake_data",
            "remaining_daily_questions",
            "can_ask_question",
            "status",
            "started_at",
            "ended_at",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "user",
            "status",
            "started_at",
            "ended_at",
            "created_at",
        ]

    def get_remaining_daily_questions(self, obj):
        """Show remaining daily questions across all sessions"""
        daily_quota = DailyQuestionQuota.get_or_create_today(obj.user)
        return daily_quota.remaining_questions()

    def get_can_ask_question(self, obj):
        """Can user ask more questions today?"""
        daily_quota = DailyQuestionQuota.get_or_create_today(obj.user)
        return daily_quota.can_ask_question() and obj.is_active()


class ChatMessageSerializer(serializers.ModelSerializer):

    class Meta:
        model = ChatMessage
        fields = "__all__"
        read_only_fields = [
            "id",
            "sequence_number",
            "created_at",
        ]


class UserQuestionInputSerializer(serializers.Serializer):
    question = serializers.CharField(
        max_length=1000,
        required=True,
    )
    session_id = serializers.PrimaryKeyRelatedField(
        queryset=ChatSession.objects.none(),
        required=False,
        allow_null=True,
        error_messages={
            "does_not_exist": "You've reached the maximum of 4 questions per session. Please start a new chat to continue.",
            "invalid": "You've reached the maximum of 4 questions per session. Please start a new chat to continue.",
        },
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request and request.user:
            self.fields["session_id"].queryset = ChatSession.objects.select_related("user", "intake_data").filter(
                user=request.user, status=SESSION_ACTIVE
            )

    def validate_question(self, value):
        """Validate question is not empty"""
        if not value or not value.strip():
            raise serializers.ValidationError("Question cannot be empty")
        return value.strip()


class UserMCQResponseSerializer(serializers.Serializer):
    mcq_message_id = serializers.UUIDField(
        required=True, help_text="ID of the MCQ question message"
    )

    selected_value = serializers.CharField(
        max_length=200,
        required=True,
    )

    def validate(self, data):
        request = self.context.get("request")

        try:
            mcq_message = ChatMessage.objects.select_related("session").get(
                id=data["mcq_message_id"]
            )
        except ChatMessage.DoesNotExist:
            raise serializers.ValidationError("MCQ message not found")

        if mcq_message.session.user != request.user:
            raise serializers.ValidationError("Unauthorized access to this session")

        if mcq_message.session.status != SESSION_ACTIVE:
            raise serializers.ValidationError(
                "You've reached the maximum of 4 questions per session. Please start a new chat to continue."
            )

        if not mcq_message.mcq_options:
            raise serializers.ValidationError("This is not an MCQ question")

        options = mcq_message.mcq_options.get("options", [])

        if data["selected_value"] not in options:
            raise serializers.ValidationError(
                f"Invalid option. Valid options are: {', '.join(options)}"
            )

        return data


class ChatHistorySerializer(serializers.ModelSerializer):

    class Meta:
        model = ChatMessage
        fields = [
            "id",
            "sequence_number",
            "sender",
            "message_text",
            "message_type",
            "suggested_questions",
            "mcq_options",
            "mcq_selected_option",
            "created_at",
        ]


class SessionListSerializer(serializers.ModelSerializer):

    title = serializers.SerializerMethodField()

    class Meta:
        model = ChatSession
        fields = [
            "id",
            "title",
            "started_at",
            "status",
        ]

    def get_title(self, obj):
        """Get session title or fallback"""
        return obj.title or "New Chat"


class UpdateSessionTitleSerializer(serializers.Serializer):
    title = serializers.CharField(
        max_length=200,
        required=True,
        allow_blank=False,
    )

    def validate_title(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Title cannot be empty")
        return value.strip()
