"""User models."""

from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.common.constants import LANG_CHOICES, LANG_UZ


class User(AbstractUser):
    """
    Custom user model extending Django's AbstractUser.
    Maps Telegram users to internal users.
    """

    telegram_id = models.BigIntegerField(unique=True, null=True, blank=True)
    username = models.CharField(
        max_length=40, unique=True, blank=True, default="", help_text="Telegram username"
    )
    first_name = models.CharField(max_length=40, blank=True, default="")
    last_name = models.CharField(max_length=40, blank=True, default="")
    user_name = models.CharField(
        max_length=40, blank=True, default="", help_text="Telegram display name"
    )
    phone = models.CharField(max_length=20, blank=True, default="")
    language = models.CharField(
        max_length=5,
        choices=LANG_CHOICES,
        default=LANG_UZ,
        help_text="User interface language preference",
    )
    resume_credits = models.IntegerField(default=0, help_text="Number of resumes user can generate")
    weekly_ai_calls = models.IntegerField(default=0, help_text="AI generation calls used this week")
    weekly_ai_calls_reset = models.DateTimeField(
        null=True, blank=True, help_text="When the weekly AI call counter was last reset"
    )
    preferred_regions = models.JSONField(
        default=list,
        blank=True,
        help_text="List of preferred region slugs (empty = all regions)",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "users"
        indexes = [
            models.Index(fields=["telegram_id"]),
            models.Index(fields=["username"]),
        ]

    def __str__(self):
        return f"{self.get_full_name()} ({self.username})"
