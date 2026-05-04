"""Subscriptions models."""

import uuid

from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class SubscriptionPlan(models.Model):
    """Subscription plans available to users."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plan_id = models.CharField(
        max_length=50, unique=True, help_text="Unique plan identifier (e.g., 'monthly')"
    )
    name = models.CharField(max_length=100, help_text="Plan name (e.g., 'Monthly Plan')")
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price in USD")
    currency = models.CharField(max_length=3, default="USD")
    duration_days = models.IntegerField(help_text="Duration in days (0 for free)")
    description = models.TextField(blank=True, default="")
    features = models.JSONField(default=list, help_text="List of features included")
    resume_credits = models.IntegerField(
        default=0, help_text="Number of resumes user can generate with this plan"
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "subscription_plans"
        ordering = ["price"]

    def __str__(self):
        return f"{self.name} (${self.price})"


class Subscription(models.Model):
    """User subscriptions."""

    STATUS_CHOICES = [
        ("active", "Active"),
        ("expired", "Expired"),
        ("cancelled", "Cancelled"),
        ("pending", "Pending"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="subscriptions")
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    activated_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    payment_id = models.CharField(
        max_length=100, blank=True, default="", help_text="External payment ID"
    )
    notes = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "subscriptions"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.plan.name} ({self.status})"

    @property
    def is_active(self):
        """Check if subscription is currently active."""
        from django.utils import timezone

        return (
            self.status == "active"
            and self.activated_at
            and self.expires_at
            and self.expires_at > timezone.now()
        )
