from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

from accounts.constants import (
    DEFAULT_LANGUAGE,
    LANGUAGE_CHOICES,
    LENGTH_CHOICES,
    LENGTH_MODERATE,
    PURPOSE_CHOICES,
    TONE_CHOICES,
    TONE_FRIENDLY,
)


class User(AbstractUser):
    preferred_language = models.CharField(
        max_length=5, choices=LANGUAGE_CHOICES, default=DEFAULT_LANGUAGE
    )
    has_set_preferences = models.BooleanField(default=False)

    def __str__(self):
        return self.email or self.username


class UserOTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp_code = models.CharField(max_length=6)
    purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES)
    otp_created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        expiry_time = self.otp_created_at + timedelta(
            minutes=getattr(settings, "OTP_EXPIRY_MINUTES", 10)
        )
        return timezone.now() > expiry_time

    def __str__(self):
        return f"{self.user.email} - {self.purpose} - {self.otp_code}"


class SystemConfiguration(models.Model):
    response_tone = models.CharField(
        max_length=20,
        choices=TONE_CHOICES,
        default=TONE_FRIENDLY,
    )

    response_length = models.CharField(
        max_length=20,
        choices=LENGTH_CHOICES,
        default=LENGTH_MODERATE,
    )

    max_daily_questions = models.PositiveIntegerField(
        default=10
    )

    additional_context = models.TextField(
        blank=True,
        default="",
        help_text="Additional context or information to include in bot responses",
    )

    custom_instructions = models.TextField(
        blank=True, default="", help_text="Custom instructions for the bot behavior"
    )

    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="config_updates",
    )

    def __str__(self):
        return f"System Configuration (Updated: {self.updated_at})"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_config(cls):
        config, created = cls.objects.get_or_create(pk=1)
        return config
