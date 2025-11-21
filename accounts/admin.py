from django.contrib import admin

from .models import UserOTP


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
