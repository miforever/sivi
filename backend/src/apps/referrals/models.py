"""Referrals models."""

import secrets
import uuid

from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Referral(models.Model):
    """Referral tracking for users."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="referral")
    referral_code = models.CharField(max_length=20, unique=True, db_index=True)

    total_referrals = models.IntegerField(default=0)
    total_commission = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "referrals"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.referral_code}"

    @staticmethod
    def generate_code():
        """Generate a unique referral code."""
        while True:
            code = secrets.token_urlsafe(8)[:8].upper()
            if not Referral.objects.filter(referral_code=code).exists():
                return code


class ReferralSignup(models.Model):
    """Track signups via referral links."""

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("active", "Active"),
        ("cancelled", "Cancelled"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    referral_code = models.CharField(max_length=20, db_index=True)
    referrer = models.ForeignKey(
        Referral, on_delete=models.CASCADE, related_name="signups", null=True, blank=True
    )
    referred_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="referred_by", null=True, blank=True
    )

    signup_date = models.DateTimeField(auto_now_add=True)
    subscription_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    # Commission details
    commission_earned = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    commission_paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "referral_signups"
        ordering = ["-signup_date"]
        indexes = [
            models.Index(fields=["referral_code"]),
            models.Index(fields=["referred_user"]),
        ]

    def __str__(self):
        return f"{self.referral_code} -> {self.referred_user}"
