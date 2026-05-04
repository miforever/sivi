"""Referrals serializers."""

from rest_framework import serializers

from apps.referrals.models import Referral, ReferralSignup


class ReferralSerializer(serializers.ModelSerializer):
    """Serializer for Referral model."""

    class Meta:
        model = Referral
        fields = [
            "id",
            "user",
            "referral_code",
            "total_referrals",
            "total_commission",
            "created_at",
        ]
        read_only_fields = ["id", "total_referrals", "total_commission", "created_at"]


class ReferralSignupSerializer(serializers.ModelSerializer):
    """Serializer for ReferralSignup model."""

    class Meta:
        model = ReferralSignup
        fields = [
            "id",
            "referral_code",
            "referred_user",
            "signup_date",
            "subscription_status",
            "commission_earned",
            "commission_paid",
        ]
        read_only_fields = ["id", "signup_date"]


class ReferralInfoSerializer(serializers.Serializer):
    """Serializer for referral info response."""

    referral_code = serializers.CharField()
    total_referrals = serializers.IntegerField()
    commission_earned = serializers.DecimalField(max_digits=10, decimal_places=2)
    commission_pending = serializers.DecimalField(max_digits=10, decimal_places=2)
