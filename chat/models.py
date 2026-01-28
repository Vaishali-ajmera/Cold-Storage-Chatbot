import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone

from chat.constants import (
    MESSAGE_TYPE_CHOICES,
    SENDER_BOT,
    SENDER_CHOICES,
    SESSION_ACTIVE,
    SESSION_STATUS_CHOICES,
)
from usecase_engine.models import UserInput


def get_max_daily_questions():
    """
    Get the configured max daily questions from system config.
    Import here to avoid circular imports.
    """
    try:
        from accounts.models import SystemConfiguration

        config = SystemConfiguration.get_config()
        return config.max_daily_questions
    except Exception:
        # Fallback if config not yet created
        return 10


class DailyQuestionQuota(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="daily_quotas",
    )

    date = models.DateField(
        help_text="The date for which this quota applies (local date)"
    )

    question_count = models.PositiveIntegerField(
        default=0, help_text="Number of questions asked on this date"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["user", "date"]
        ordering = ["-date"]

    def __str__(self):
        max_questions = get_max_daily_questions()
        return (
            f"{self.user.username} - {self.date}: {self.question_count}/{max_questions}"
        )

    def can_ask_question(self):
        """Check if user can ask more questions today"""
        max_questions = get_max_daily_questions()
        return self.question_count < max_questions

    def remaining_questions(self):
        """Get the number of questions remaining for today"""
        max_questions = get_max_daily_questions()
        return max(0, max_questions - self.question_count)

    def increment_count(self):
        """Increment the daily question count"""
        self.question_count += 1
        self.save(update_fields=["question_count", "updated_at"])

    @classmethod
    def get_or_create_today(cls, user):
        """Get or create today's quota record for a user"""
        today = timezone.now().date()
        quota, created = cls.objects.get_or_create(
            user=user, date=today, defaults={"question_count": 0}
        )
        return quota


class ChatSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_sessions",
    )

    intake_data = models.ForeignKey(
        UserInput,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="chat_sessions",
    )

    title = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        help_text="Auto-generated session title from first question",
    )

    llm_context_history = models.JSONField(
        default=list,
        blank=True,
        help_text="Pre-computed chat history for LLM context (excludes META/OUT_OF_CONTEXT)",
    )

    status = models.CharField(
        max_length=20, choices=SESSION_STATUS_CHOICES, default=SESSION_ACTIVE
    )

    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-started_at"]
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["status", "started_at"]),
        ]

    def __str__(self):
        return f"{self.user.username} - ChatSession {self.id}"

    def is_active(self):
        return self.status == SESSION_ACTIVE

    def get_llm_context(self, limit=10):
        history = self.llm_context_history or []
        return history[-limit:] if len(history) > limit else history

    def append_to_llm_context(self, sender: str, message: str):
        if self.llm_context_history is None:
            self.llm_context_history = []

        self.llm_context_history.append({"sender": sender, "message": message})

        # Keep only last 20 messages to prevent unlimited growth
        if len(self.llm_context_history) > 20:
            self.llm_context_history = self.llm_context_history[-20:]

        self.save(update_fields=["llm_context_history"])

    def set_title_from_question(self, question):
        """Auto-generate session title from first question"""
        if not self.title and question:
            self.title = (question[:50] + "...") if len(question) > 50 else question
            self.save(update_fields=["title"])


class ChatMessage(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name="messages",
    )

    sequence_number = models.PositiveIntegerField(
        help_text="Sequential message number within session (1, 2, 3...)"
    )

    sender = models.CharField(max_length=10, choices=SENDER_CHOICES)

    message_text = models.TextField(help_text="The actual message content")

    message_type = models.CharField(
        max_length=30,
        choices=MESSAGE_TYPE_CHOICES,
        help_text="Type of message for flow control",
    )

    suggested_questions = models.JSONField(
        null=True,
        blank=True,
    )

    mcq_options = models.JSONField(
        null=True,
        blank=True,
    )

    mcq_selected_option = models.CharField(
        max_length=10,
        null=True,
        blank=True,
    )

    # Parent-child relationship for MCQ flow
    parent_message = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="responses",
        help_text="Links MCQ response to the MCQ question",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["session", "sequence_number"]
        unique_together = ["session", "sequence_number"]
        indexes = [
            models.Index(fields=["session", "sequence_number"]),
            models.Index(fields=["session", "message_type"]),
            models.Index(fields=["parent_message"]),
            models.Index(fields=["created_at"]),
        ]
        verbose_name = "Chat Message"
        verbose_name_plural = "Chat Messages"

    def __str__(self):
        return f"[{self.session.user.username}] #{self.sequence_number}: {self.get_sender_display()}"

    def save(self, *args, **kwargs):
        """Auto-set sequence number if not provided"""
        if not self.sequence_number:
            last_message = (
                ChatMessage.objects.filter(session=self.session)
                .order_by("-sequence_number")
                .first()
            )

            self.sequence_number = (
                (last_message.sequence_number + 1) if last_message else 1
            )

        super().save(*args, **kwargs)
