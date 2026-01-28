from rest_framework import serializers

from accounts.models import SystemConfiguration


class SystemConfigurationSerializer(serializers.ModelSerializer):

    class Meta:
        model = SystemConfiguration
        fields = [
            "response_tone",
            "response_length",
            "max_daily_questions",
            "additional_context",
            "custom_instructions",
            "updated_at",
        ]
        read_only_fields = ["updated_at"]

    def validate_max_daily_questions(self, value):
        if value < 1:
            raise serializers.ValidationError("Max daily questions must be at least 1.")
        if value > 1000:
            raise serializers.ValidationError("Max daily questions cannot exceed 1000.")
        return value


class SystemConfigurationChoicesSerializer(serializers.Serializer):

    tone_choices = serializers.SerializerMethodField()
    length_choices = serializers.SerializerMethodField()

    def get_tone_choices(self, obj):
        from accounts.constants import TONE_CHOICES

        return [{"value": choice[0], "label": choice[1]} for choice in TONE_CHOICES]

    def get_length_choices(self, obj):
        from accounts.constants import LENGTH_CHOICES

        return [{"value": choice[0], "label": choice[1]} for choice in LENGTH_CHOICES]


class AdminStatsSerializer(serializers.Serializer):

    total_users = serializers.IntegerField()
    total_sessions = serializers.IntegerField()
    total_messages = serializers.IntegerField()
    questions_today = serializers.IntegerField()
    avg_questions_per_user = serializers.FloatField()
