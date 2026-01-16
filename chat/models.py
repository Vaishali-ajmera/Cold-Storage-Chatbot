import uuid

from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from chat.constants import (
    DEFAULT_MAX_QUESTIONS,
    MESSAGE_TYPE_CHOICES,
    SENDER_BOT,
    SENDER_CHOICES,
    SESSION_ACTIVE,
    SESSION_LIMIT_REACHED,
    SESSION_STATUS_CHOICES,
)
from usecase_engine.models import UserInput


class ChatSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        User,
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

    user_questions_count = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
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

    def can_accept_question(self):
        """Check if session can accept more questions"""
        return (
            self.status == SESSION_ACTIVE
            and self.user_questions_count < DEFAULT_MAX_QUESTIONS
        )

    def remaining_questions(self):
        """Calculate remaining questions allowed"""
        return max(0, DEFAULT_MAX_QUESTIONS - self.user_questions_count)

    def increment_question_count(self):
        """Safely increment user question counter"""
        self.user_questions_count += 1

        if self.user_questions_count >= DEFAULT_MAX_QUESTIONS:
            self.status = SESSION_LIMIT_REACHED
            self.ended_at = timezone.now()

        self.save()

    def get_llm_context(self, limit=10):
        """
        Get pre-computed LLM context history.
        No DB queries, no filtering - just return the stored context.
        """
        history = self.llm_context_history or []
        # Return last N messages to keep context window manageable
        return history[-limit:] if len(history) > limit else history

    def append_to_llm_context(self, sender: str, message: str):
        """
        Append a message to the LLM context history.
        Should only be called for ANSWER_DIRECTLY and MCQ conversations.
        """
        if self.llm_context_history is None:
            self.llm_context_history = []
        
        self.llm_context_history.append({
            "sender": sender,
            "message": message
        })
        
        # Keep only last 20 messages to prevent unlimited growth
        if len(self.llm_context_history) > 20:
            self.llm_context_history = self.llm_context_history[-20:]
        
        self.save(update_fields=["llm_context_history"])

    def get_chat_history(self, limit=10):
        """
        DEPRECATED: Use get_llm_context() instead.
        Kept for backward compatibility with existing code.
        """
        messages = self.messages.order_by("-sequence_number")[:limit].values(
            "sender", "message_text"
        )
        return [
            {"sender": msg["sender"], "message": msg["message_text"]}
            for msg in reversed(list(messages))
        ]

    def set_title_from_question(self, question):
        """Auto-generate session title from first question"""
        if not self.title and question:
            self.title = (question[:50] + "...") if len(question) > 50 else question
            self.save(update_fields=["title"])

    def get_last_message_preview(self, max_length=80):
        """Get preview of the last bot message"""
        last_bot_message = (
            self.messages.filter(sender=SENDER_BOT).order_by("-sequence_number").first()
        )

        if last_bot_message:
            text = last_bot_message.message_text
            return (text[:max_length] + "...") if len(text) > max_length else text

        return None


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
