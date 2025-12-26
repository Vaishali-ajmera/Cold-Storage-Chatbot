from django.contrib import admin
from django.utils.html import format_html

from chat.models import ChatMessage, ChatSession


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
        "status",
        "user_questions_count",
    )

    list_filter = (
        "status",
        "started_at",
    )

    search_fields = (
        "id",
        "user__username",
        "user__email",
    )

    readonly_fields = (
        "id",
        "user",
        "intake_data",
        "user_questions_count",
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

    list_filter = (
        "sender",
        "message_type",
        "created_at",
    )

    search_fields = (
        "message_text",
        "session__id",
        "session__user__username",
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
