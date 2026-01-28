from django.conf import settings
from django.db import models

from usecase_engine.constants import USER_CHOICES


class UserInput(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cold_storage_intakes",
    )

    user_choice = models.CharField(max_length=30, choices=USER_CHOICES)

    intake_data = models.JSONField(
        default=dict,
        blank=True,
    )
    suggestions = models.JSONField(
        default=list,
        blank=True,
    )
    welcome_message = models.TextField(
        blank=True,
        null=True,
    )
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_user_choice_display()}"

    class Meta:
        ordering = ["-created_at"]
