"""Referrals views."""

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny

from apps.common.responses import error_response, success_response
from apps.referrals.models import Referral, ReferralSignup
from apps.referrals.serializers import (
    ReferralSerializer,
    ReferralSignupSerializer,
)

REFERRAL_COMMISSION_PERCENT = 10  # 10% commission per signup


class ReferralViewSet(viewsets.ModelViewSet):
    """ViewSet for managing referrals."""

    queryset = Referral.objects.all()
    serializer_class = ReferralSerializer
    permission_classes = [AllowAny]

    @action(detail=False, methods=["post"])
    def create_link(self, request):
        """Create a referral link for a user."""
        user_id = request.data.get("user_id")

        if not user_id:
            return error_response(
                code="MISSING_USER",
                message="user_id is required",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        from apps.users.models import User

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return error_response(
                code="USER_NOT_FOUND",
                message="User not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        # Create or get existing referral
        referral, created = Referral.objects.get_or_create(
            user=user, defaults={"referral_code": Referral.generate_code()}
        )

        return success_response(
            data={
                "referral_code": referral.referral_code,
                "referral_link": f"https://api.example.com/refer/{referral.referral_code}",
            },
            status_code=status.HTTP_200_OK if not created else status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["get"])
    def info(self, request):
        """Get referral info for a user."""
        user_id = request.query_params.get("user_id")

        if not user_id:
            return error_response(
                code="MISSING_USER",
                message="user_id query parameter is required",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        try:
            from apps.users.models import User

            user = User.objects.get(id=user_id)
            referral = Referral.objects.get(user=user)
        except (User.DoesNotExist, Referral.DoesNotExist):
            return error_response(
                code="REFERRAL_NOT_FOUND",
                message="Referral not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        # Calculate pending commission
        pending_signups = referral.signups.filter(commission_paid=False)
        pending_commission = sum(s.commission_earned for s in pending_signups)

        return success_response(
            data={
                "referral_code": referral.referral_code,
                "total_referrals": referral.total_referrals,
                "commission_earned": str(referral.total_commission),
                "commission_pending": str(pending_commission),
            },
            status_code=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["get"])
    def list_referrals(self, request):
        """List referred users."""
        user_id = request.query_params.get("user_id")

        if not user_id:
            return error_response(
                code="MISSING_USER",
                message="user_id query parameter is required",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        try:
            from apps.users.models import User

            user = User.objects.get(id=user_id)
            referral = Referral.objects.get(user=user)
        except (User.DoesNotExist, Referral.DoesNotExist):
            return error_response(
                code="REFERRAL_NOT_FOUND",
                message="Referral not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        signups = referral.signups.all()
        serializer = ReferralSignupSerializer(signups, many=True)

        return success_response(data=serializer.data, status_code=status.HTTP_200_OK)

    @action(detail=False, methods=["post"])
    def track_signup(self, request):
        """Track a new signup via referral."""
        referral_code = request.data.get("referral_code")
        new_user_id = request.data.get("new_user_id")

        if not referral_code or not new_user_id:
            return error_response(
                code="MISSING_DATA",
                message="referral_code and new_user_id are required",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        try:
            from apps.users.models import User

            referral = Referral.objects.get(referral_code=referral_code)
            new_user = User.objects.get(id=new_user_id)
        except (Referral.DoesNotExist, User.DoesNotExist):
            return error_response(
                code="NOT_FOUND",
                message="Referral or user not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        # Create signup record
        signup = ReferralSignup.objects.create(
            referral_code=referral_code,
            referrer=referral,
            referred_user=new_user,
            subscription_status="pending",
        )

        return success_response(
            data=ReferralSignupSerializer(signup).data, status_code=status.HTTP_201_CREATED
        )

    @action(detail=False, methods=["post"])
    def redeem_commission(self, request):
        """Redeem earned commissions."""
        user_id = request.data.get("user_id")

        if not user_id:
            return error_response(
                code="MISSING_USER",
                message="user_id is required",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        try:
            from django.utils import timezone

            from apps.users.models import User

            user = User.objects.get(id=user_id)
            referral = Referral.objects.get(user=user)
        except (User.DoesNotExist, Referral.DoesNotExist):
            return error_response(
                code="REFERRAL_NOT_FOUND",
                message="Referral not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        # Mark pending commissions as paid
        pending_signups = referral.signups.filter(commission_paid=False)
        total_redeemed = 0

        for signup in pending_signups:
            signup.commission_paid = True
            signup.paid_at = timezone.now()
            signup.save()
            total_redeemed += signup.commission_earned

        return success_response(
            data={
                "amount_redeemed": str(total_redeemed),
                "signups_redeemed": pending_signups.count(),
            },
            status_code=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["get"])
    def rewards_config(self, request):
        """Get referral rewards configuration."""
        return success_response(
            data={
                "commission_percent": REFERRAL_COMMISSION_PERCENT,
                "description": "Get 10% commission on each referred user subscription",
            },
            status_code=status.HTTP_200_OK,
        )
