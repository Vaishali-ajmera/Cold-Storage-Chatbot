from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

from accounts.constants import DEFAULT_LANGUAGE, LANGUAGE_CHOICES, PURPOSE_CHOICES


class User(AbstractUser):
    preferred_language = models.CharField(
        max_length=5,
        choices=LANGUAGE_CHOICES,
        default=DEFAULT_LANGUAGE
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
