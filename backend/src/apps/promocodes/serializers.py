"""Promocodes serializers."""

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.promocodes.models import Promocode, PromoCodeUsage


class PromocodeSerializer(serializers.ModelSerializer):
    """Serializer for Promocode model."""

    is_valid = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()
    remaining_uses = serializers.SerializerMethodField()

    class Meta:
        model = Promocode
        fields = [
            "id",
            "code",
            "description",
            "discount_percent",
            "discount_amount",
            "max_uses",
            "used_count",
            "remaining_uses",
            "applicable_plans",
            "valid_from",
            "valid_until",
            "is_active",
            "is_valid",
            "is_expired",
            "created_at",
        ]
        read_only_fields = ["id", "used_count", "created_at"]

    @extend_schema_field(serializers.IntegerField)
    def get_is_valid(self, obj):
        return obj.is_valid

    @extend_schema_field(serializers.BooleanField)
    def get_is_expired(self, obj):
        return obj.is_expired

    @extend_schema_field(serializers.BooleanField)
    def get_remaining_uses(self, obj):
        if obj.max_uses == 0:
            return None
        return max(0, obj.max_uses - obj.used_count)


class PromocodeValidationSerializer(serializers.Serializer):
    """Serializer for validating a promocode."""

    code = serializers.CharField(required=True)
    plan_id = serializers.CharField(required=False, allow_blank=True)


class PromocodeApplySerializer(serializers.Serializer):
    """Serializer for applying a promocode."""

    code = serializers.CharField(required=True)
    plan_id = serializers.CharField(required=False, allow_blank=True)
    user_id = serializers.CharField(required=False, allow_blank=True)


class PromoCodeUsageSerializer(serializers.ModelSerializer):
    """Serializer for PromoCodeUsage model."""

    class Meta:
        model = PromoCodeUsage
        fields = [
            "id",
            "user",
            "code",
            "subscription",
            "discount_applied",
            "used_at",
        ]
        read_only_fields = ["id", "used_at"]
