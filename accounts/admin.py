from django.contrib import admin

from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserOTP


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Preferences", {"fields": ("preferred_language", "has_set_preferences")}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("Preferences", {"fields": ("preferred_language", "has_set_preferences")}),
    )
    list_display = BaseUserAdmin.list_display + ("preferred_language", "has_set_preferences")


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
