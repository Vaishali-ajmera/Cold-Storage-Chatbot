from django.contrib.auth.models import User
from rest_framework import serializers

from chat.constants import SESSION_ACTIVE
from chat.models import ChatMessage, ChatSession


class ChatSessionSerializer(serializers.ModelSerializer):
    remaining_questions = serializers.SerializerMethodField()
    can_ask_question = serializers.SerializerMethodField()

    class Meta:
        model = ChatSession
        fields = [
            "id",
            "user",
            "intake_data",
            "user_questions_count",
            "remaining_questions",
            "can_ask_question",
            "status",
            "started_at",
            "ended_at",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "user",
            "user_questions_count",
            "status",
            "started_at",
            "ended_at",
            "created_at",
        ]

    def get_remaining_questions(self, obj):
        """Show remaining questions"""
        return obj.remaining_questions()

    def get_can_ask_question(self, obj):
        """Can user ask more questions?"""
        return obj.can_accept_question()


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
        queryset=ChatSession.objects.none(), required=False, allow_null=True
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request and request.user:
            self.fields["session_id"].queryset = ChatSession.objects.filter(
                user=request.user, status=SESSION_ACTIVE
            )

    def validate_question(self, value):
        """Validate question is not empty"""
        if not value or not value.strip():
            raise serializers.ValidationError("Question cannot be empty")
        return value.strip()


class UserMCQResponseSerializer(serializers.Serializer):
    """
    Input serializer when user answers MCQ
    """

    mcq_message_id = serializers.UUIDField(
        required=True, help_text="ID of the MCQ question message"
    )

    selected_option = serializers.CharField(
        max_length=10,
        required=True,
        help_text="Selected option key (e.g., 'A', 'B', 'C', 'D')",
    )

    selected_value = serializers.CharField(
        max_length=200,
        required=True,
        help_text="Full text of selected option (e.g., '3-6 months')",
    )

    def validate(self, data):
        """Validate MCQ response"""
        # Check if MCQ message exists
        try:
            mcq_message = ChatMessage.objects.get(id=data["mcq_message_id"])
        except ChatMessage.DoesNotExist:
            raise serializers.ValidationError("MCQ message not found")

        # Check if it's actually an MCQ question
        if not mcq_message.mcq_options:
            raise serializers.ValidationError("This is not an MCQ question")

        # Validate selected option exists in MCQ options
        options = mcq_message.mcq_options.get("options", [])
        valid_keys = [opt["key"] for opt in options]

        if data["selected_option"] not in valid_keys:
            raise serializers.ValidationError(
                f"Invalid option. Valid options are: {', '.join(valid_keys)}"
            )

        return data


class ChatHistorySerializer(serializers.ModelSerializer):
    """
    Serializer for loading chat history (conversation view)
    """

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
