from rest_framework import serializers

from usecase_engine.constants import USER_CHOICES
from usecase_engine.models import UserInput


class UserInputBaseSerializer(serializers.ModelSerializer):
    user_choice = serializers.ChoiceField(
        choices=USER_CHOICES,
        error_messages={
            "invalid_choice": "Invalid selection. Please choose either build or existing."
        },
    )

    def validate_intake_data(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("Intake_data must be a valid JSON object")
        return value


class UserInputReadSerializer(UserInputBaseSerializer):
    """Serializer for GET responses"""

    user_choice_display = serializers.CharField(
        source="get_user_choice_display", read_only=True
    )

    class Meta:
        model = UserInput
        fields = [
            "id",
            "user_choice",
            "user_choice_display",
            "intake_data",
            "created_at",
            "updated_at",
        ]


class UserInputWriteSerializer(UserInputBaseSerializer):
    """Serializer for CREATE & UPDATE"""

    class Meta:
        model = UserInput
        fields = ["user_choice", "intake_data"]

    def create(self, validated_data):
        return UserInput.objects.create(
            user=self.context["request"].user, **validated_data
        )
