from django.contrib import admin
from django.utils.html import format_html

from chat.models import ChatMessage, ChatSession, DailyQuestionQuota


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    can_delete = False
    ordering = ("sequence_number",)

    readonly_fields = (
        "id",
        "sequence_number",
        "sender",
        "message_type",
        "message_text",
        "suggested_questions",
        "mcq_options",
        "mcq_selected_option",
        "parent_message",
        "created_at",
    )

    fields = (
        "sequence_number",
        "sender",
        "message_type",
        "message_text",
        "mcq_selected_option",
        "parent_message",
        "created_at",
    )


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "title",
        "status",
        "started_at",
    )

    list_filter = (
        "status",
        "started_at",
    )

    readonly_fields = (
        "id",
        "user",
        "intake_data",
        "started_at",
        "created_at",
        "updated_at",
    )

    inlines = [ChatMessageInline]


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "session",
        "sequence_number",
        "sender",
        "message_type",
    )

    readonly_fields = (
        "id",
        "session",
        "sequence_number",
        "sender",
        "message_type",
        "message_text",
        "suggested_questions",
        "mcq_options",
        "mcq_selected_option",
        "parent_message",
        "created_at",
    )


@admin.register(DailyQuestionQuota)
class DailyQuestionQuotaAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "date",
        "question_count",
        "remaining_questions",
        "created_at",
    )

    readonly_fields = (
        "user",
        "date",
        "question_count",
        "created_at",
        "updated_at",
    )

    def remaining_questions(self, obj):
        return obj.remaining_questions()
    remaining_questions.short_description = "Remaining"
