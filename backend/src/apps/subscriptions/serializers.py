"""Subscriptions serializers."""

from django.utils import timezone
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.subscriptions.models import Subscription, SubscriptionPlan


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    """Serializer for SubscriptionPlan."""

    class Meta:
        model = SubscriptionPlan
        fields = [
            "id",
            "plan_id",
            "name",
            "price",
            "currency",
            "duration_days",
            "description",
            "features",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class SubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for Subscription."""

    plan_name = serializers.CharField(source="plan.name", read_only=True)
    is_active = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = [
            "id",
            "user",
            "plan",
            "plan_name",
            "status",
            "activated_at",
            "expires_at",
            "cancelled_at",
            "payment_id",
            "notes",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    @extend_schema_field(serializers.BooleanField)
    def get_is_active(self, obj):
        """Check if subscription is currently active."""
        return (
            obj.status == "active"
            and obj.activated_at
            and obj.expires_at
            and obj.expires_at > timezone.now()
        )


class SubscriptionActivateSerializer(serializers.Serializer):
    """Serializer for activating a subscription."""

    plan_id = serializers.CharField(required=True, help_text="Subscription plan ID")
    payment_id = serializers.CharField(required=False, allow_blank=True)

    def validate_plan_id(self, value):
        """Validate that plan exists."""
        if not SubscriptionPlan.objects.filter(plan_id=value).exists():
            raise serializers.ValidationError("Plan does not exist")
        return value


class SubscriptionRenewSerializer(serializers.Serializer):
    """Serializer for renewing a subscription."""

    payment_id = serializers.CharField(required=False, allow_blank=True)


class SubscriptionStatusSerializer(serializers.Serializer):
    """Serializer for subscription status response."""

    subscription_id = serializers.CharField()
    status = serializers.CharField()
    plan = serializers.CharField()
    expires_at = serializers.DateTimeField(allow_null=True)
    is_active = serializers.BooleanField()
