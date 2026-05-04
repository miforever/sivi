"""API call logging for external service usage tracking."""

from django.db import models


class APICallLog(models.Model):
    """Tracks external API calls (OpenAI, Fireworks, etc.)."""

    PROVIDER_CHOICES = [
        ("openai", "OpenAI"),
        ("fireworks", "Fireworks AI"),
    ]

    provider = models.CharField(max_length=30, choices=PROVIDER_CHOICES, db_index=True)
    endpoint = models.CharField(max_length=255)
    tokens_used = models.IntegerField(default=0)
    cost = models.DecimalField(max_digits=10, decimal_places=6, default=0)
    response_time_ms = models.IntegerField(default=0)
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["provider", "created_at"]),
        ]

    def __str__(self):
        return f"{self.provider} - {self.endpoint} - {self.created_at}"


class UserEvent(models.Model):
    """Tracks user-triggered events from the telegram bot."""

    EVENT_CHOICES = [
        ("job_feed_scroll", "Job Feed Scroll"),
    ]

    event_type = models.CharField(max_length=50, choices=EVENT_CHOICES, db_index=True)
    telegram_id = models.BigIntegerField(db_index=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["event_type", "created_at"]),
        ]

    def __str__(self):
        return f"{self.event_type} - {self.telegram_id} - {self.created_at}"
