"""Store models for credit purchases and transactions."""

from django.db import models

from apps.users.models import User


class CreditPackage(models.Model):
    """Available credit packages for purchase."""

    credits = models.IntegerField(unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="UZS")
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "credit_packages"
        ordering = ["credits"]

    def __str__(self):
        return f"{self.credits} credits - {self.price} {self.currency}"


class CreditTransaction(models.Model):
    """Record of all credit transactions (purchases and usage)."""

    TRANSACTION_TYPE_CHOICES = [
        ("purchase", "Purchase"),
        ("usage", "Usage"),
        ("refund", "Refund"),
        ("bonus", "Bonus"),
        ("admin_adjustment", "Admin Adjustment"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("refunded", "Refunded"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="credit_transactions")
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    credits = models.IntegerField(help_text="Positive for add, negative for deduct")
    balance_after = models.IntegerField(help_text="User's balance after this transaction")

    # Purchase-specific fields
    package = models.ForeignKey(
        CreditPackage, on_delete=models.SET_NULL, null=True, blank=True, related_name="transactions"
    )
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, null=True, blank=True)
    payment_provider = models.CharField(
        max_length=50, default="click", help_text="Payment provider used (click, payme, etc.)"
    )
    payment_id = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        help_text="External payment provider transaction ID",
    )

    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    # Usage-specific fields (when type='usage')
    resume_id = models.IntegerField(
        null=True, blank=True, help_text="Resume ID if credits used for resume generation"
    )

    # Additional info
    notes = models.TextField(blank=True, help_text="Admin notes or error messages")
    metadata = models.JSONField(
        default=dict, blank=True, help_text="Additional data (invoice payload, etc.)"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "credit_transactions"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["payment_id"]),
            models.Index(fields=["transaction_type", "status"]),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.transaction_type} - {self.credits} credits"


class PaymentWebhook(models.Model):
    """Log of payment provider webhooks for debugging."""

    provider = models.CharField(max_length=50)
    payload = models.JSONField()
    status_code = models.IntegerField(null=True, blank=True)
    processed = models.BooleanField(default=False)
    transaction = models.ForeignKey(
        CreditTransaction, on_delete=models.SET_NULL, null=True, blank=True, related_name="webhooks"
    )
    error_message = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "payment_webhooks"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.provider} - {self.created_at}"
