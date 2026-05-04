"""Subscriptions views."""

from datetime import timedelta

from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from apps.common.authentication import ApiKeyAuthentication, TelegramBotAuthentication
from apps.common.responses import error_response, success_response
from apps.subscriptions.models import Subscription, SubscriptionPlan
from apps.subscriptions.serializers import (
    SubscriptionActivateSerializer,
    SubscriptionPlanSerializer,
    SubscriptionSerializer,
)


class SubscriptionPlanViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for listing subscription plans.
    """

    queryset = SubscriptionPlan.objects.filter(is_active=True)
    serializer_class = SubscriptionPlanSerializer

    authentication_classes = [ApiKeyAuthentication]
    permission_classes = [AllowAny]


class SubscriptionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing subscriptions.
    Supports both Telegram bot (API key + telegram_id) and Web/App (JWT) authentication.
    """

    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer

    authentication_classes = [TelegramBotAuthentication, JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["post"])
    def activate(self, request):
        """
        Activate a subscription for the authenticated user.
        Works for both Telegram bot and Web/App clients.
        """
        serializer = SubscriptionActivateSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                code="INVALID_DATA",
                message="Invalid request data",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        plan_id = serializer.validated_data["plan_id"]
        payment_id = serializer.validated_data.get("payment_id", "")

        user = request.user

        try:
            plan = SubscriptionPlan.objects.get(plan_id=plan_id, is_active=True)
        except SubscriptionPlan.DoesNotExist:
            return error_response(
                code="PLAN_NOT_FOUND",
                message="Subscription plan not found or inactive",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        user.resume_credits += plan.resume_credits
        user.save()

        # Cancel any existing active subscriptions
        Subscription.objects.filter(user=user, status="active").update(
            status="cancelled", cancelled_at=timezone.now()
        )

        # Create new subscription
        now = timezone.now()
        expires_at = now + timedelta(days=plan.duration_days) if plan.duration_days > 0 else None

        subscription = Subscription.objects.create(
            user=user,
            plan=plan,
            status="active",
            activated_at=now,
            expires_at=expires_at,
            payment_id=payment_id,
        )

        data = SubscriptionSerializer(subscription).data
        data["has_active_subscription"] = True

        return success_response(data=data, status_code=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"])
    def status(self, request):
        """
        Get subscription status for the authenticated user.
        Works for both Telegram bot and Web/App clients.
        """
        user = request.user

        # Get active subscription
        subscription = (
            Subscription.objects.filter(user=user, status="active")
            .order_by("-activated_at")
            .first()
        )

        if not subscription:
            return success_response(
                data={"status": "no_subscription", "has_active_subscription": False},
                status_code=status.HTTP_200_OK,
            )

        # Check if subscription is actually still valid
        if subscription.expires_at and subscription.expires_at < timezone.now():
            subscription.status = "expired"
            subscription.save()
            return success_response(
                data={"status": "expired", "has_active_subscription": False},
                status_code=status.HTTP_200_OK,
            )

        return success_response(
            data={**SubscriptionSerializer(subscription).data, "has_active_subscription": True},
            status_code=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["post"])
    def renew(self, request):
        """
        Renew the authenticated user's subscription.
        Works for both Telegram bot and Web/App clients.
        """
        payment_id = request.data.get("payment_id", "")
        user = request.user

        # Get current subscription
        subscription = Subscription.objects.filter(user=user).order_by("-activated_at").first()

        if not subscription:
            return error_response(
                code="NO_SUBSCRIPTION",
                message="User has no subscription to renew",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        # Cancel old subscription if active
        if subscription.status == "active":
            subscription.status = "cancelled"
            subscription.cancelled_at = timezone.now()
            subscription.save()

        # Create new subscription with same plan
        now = timezone.now()
        expires_at = (
            now + timedelta(days=subscription.plan.duration_days)
            if subscription.plan.duration_days > 0
            else None
        )

        new_subscription = Subscription.objects.create(
            user=user,
            plan=subscription.plan,
            status="active",
            activated_at=now,
            expires_at=expires_at,
            payment_id=payment_id,
        )

        data = SubscriptionSerializer(new_subscription).data
        data["has_active_subscription"] = True

        return success_response(data=data, status_code=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"])
    def cancel(self, request):
        """
        Cancel the authenticated user's subscription.
        Works for both Telegram bot and Web/App clients.
        """
        user = request.user

        # Get active subscription
        subscription = (
            Subscription.objects.filter(user=user, status="active")
            .order_by("-activated_at")
            .first()
        )

        if not subscription:
            return error_response(
                code="NO_ACTIVE_SUBSCRIPTION",
                message="User has no active subscription to cancel",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        # Cancel subscription
        subscription.status = "cancelled"
        subscription.cancelled_at = timezone.now()
        subscription.save()

        return success_response(
            data=SubscriptionSerializer(subscription).data, status_code=status.HTTP_200_OK
        )
