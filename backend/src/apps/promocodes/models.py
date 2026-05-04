"""Promocodes models."""

import uuid

from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Promocode(models.Model):
    """Promotional codes for discounts."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True, db_index=True)
    description = models.TextField(blank=True, default="")

    # Discount options
    discount_percent = models.IntegerField(default=0, help_text="Discount percentage (0-100)")
    discount_amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True, help_text="Fixed discount amount"
    )

    # Usage limits
    max_uses = models.IntegerField(default=0, help_text="Maximum uses (0 = unlimited)")
    used_count = models.IntegerField(default=0)

    # Plans this code applies to
    applicable_plans = models.JSONField(
        default=list, help_text="List of plan IDs this code applies to (empty = all)"
    )

    # Validity
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_until = models.DateTimeField(null=True, blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "promocodes"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return f"{self.code} - {self.discount_percent}%"

    @property
    def is_expired(self):
        """Check if promocode is expired."""
        from django.utils import timezone

        if self.valid_until:
            return timezone.now() > self.valid_until
        return False

    @property
    def is_valid(self):
        """Check if promocode can be used."""
        from django.utils import timezone

        if not self.is_active:
            return False
        if self.is_expired:
            return False
        if self.max_uses > 0 and self.used_count >= self.max_uses:
            return False
        if self.valid_from and timezone.now() < self.valid_from:
            return False
        return True


class PromoCodeUsage(models.Model):
    """Track usage of promotional codes."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="promocode_usages")
    code = models.CharField(max_length=50, db_index=True)
    promocode = models.ForeignKey(Promocode, on_delete=models.SET_NULL, null=True, blank=True)

    # Which subscription this was used for
    subscription = models.ForeignKey(
        "subscriptions.Subscription",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="promocode_usages",
    )

    discount_applied = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    used_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "promocode_usages"
        ordering = ["-used_at"]
        indexes = [
            models.Index(fields=["user", "code"]),
            models.Index(fields=["code"]),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.code}"
