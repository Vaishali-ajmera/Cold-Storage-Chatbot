from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import SystemConfiguration, User, UserOTP


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Preferences", {"fields": ("preferred_language", "has_set_preferences")}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("Preferences", {"fields": ("preferred_language", "has_set_preferences")}),
    )
    list_display = BaseUserAdmin.list_display + (
        "preferred_language",
        "has_set_preferences",
        "is_staff",
    )


@admin.register(UserOTP)
class UserOTPAdmin(admin.ModelAdmin):
    list_display = ("user", "otp_code", "purpose", "otp_created_at", "is_expired")
    list_filter = ("purpose", "otp_created_at")
    search_fields = ("user__username", "user__email", "otp_code")
    readonly_fields = ("otp_code", "otp_created_at", "is_expired")
    ordering = ("-otp_created_at",)

    def is_expired(self, obj):
        return obj.is_expired()

    is_expired.boolean = True
    is_expired.short_description = "Expired?"


@admin.register(SystemConfiguration)
class SystemConfigurationAdmin(admin.ModelAdmin):
    list_display = (
        "response_tone",
        "response_length",
        "max_daily_questions",
        "updated_at",
        "updated_by",
    )
    readonly_fields = ("updated_at",)
    fieldsets = (
        ("Response Settings", {"fields": ("response_tone", "response_length")}),
        ("Limits", {"fields": ("max_daily_questions",)}),
        (
            "Custom Content",
            {
                "fields": ("additional_context", "custom_instructions"),
                "classes": ("collapse",),
            },
        ),
        (
            "Metadata",
            {"fields": ("updated_at", "updated_by"), "classes": ("collapse",)},
        ),
    )

    def has_add_permission(self, request):
        return not SystemConfiguration.objects.exists()

    # def has_delete_permission(self, request, obj=None):
    #     # Prevent deleting the config
    #     return False
