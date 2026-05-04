"""Promocodes views."""

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny

from apps.common.responses import error_response, success_response
from apps.promocodes.models import Promocode, PromoCodeUsage
from apps.promocodes.serializers import (
    PromocodeApplySerializer,
    PromocodeSerializer,
    PromoCodeUsageSerializer,
    PromocodeValidationSerializer,
)


class PromocodeViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for promotional codes."""

    queryset = Promocode.objects.filter(is_active=True)
    serializer_class = PromocodeSerializer
    permission_classes = [AllowAny]

    @action(detail=False, methods=["post"])
    def validate(self, request):
        """Validate a promocode."""
        serializer = PromocodeValidationSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                code="INVALID_DATA",
                message="Invalid request data",
                status_code=status.HTTP_400_BAD_REQUEST,
                details=serializer.errors,
            )

        code = serializer.validated_data["code"].upper()
        plan_id = serializer.validated_data.get("plan_id", "")

        try:
            promocode = Promocode.objects.get(code__iexact=code)
        except Promocode.DoesNotExist:
            return error_response(
                code="CODE_NOT_FOUND",
                message="Promocode not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        # Check if valid
        if not promocode.is_valid:
            return error_response(
                code="CODE_INVALID",
                message="Promocode is invalid or expired",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        # Check if applicable to plan
        if promocode.applicable_plans and plan_id and plan_id not in promocode.applicable_plans:
            return error_response(
                code="CODE_NOT_APPLICABLE",
                message="Promocode is not applicable to this plan",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        return success_response(
            data=PromocodeSerializer(promocode).data, status_code=status.HTTP_200_OK
        )

    @action(detail=False, methods=["get"])
    def details(self, request):
        """Get promocode details."""
        code = request.query_params.get("code")

        if not code:
            return error_response(
                code="MISSING_CODE",
                message="code query parameter is required",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        try:
            promocode = Promocode.objects.get(code__iexact=code)
        except Promocode.DoesNotExist:
            return error_response(
                code="CODE_NOT_FOUND",
                message="Promocode not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        return success_response(
            data=PromocodeSerializer(promocode).data, status_code=status.HTTP_200_OK
        )

    @action(detail=False, methods=["post"])
    def apply(self, request):
        """Apply a promocode to a subscription."""
        serializer = PromocodeApplySerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                code="INVALID_DATA",
                message="Invalid request data",
                status_code=status.HTTP_400_BAD_REQUEST,
                details=serializer.errors,
            )

        code = serializer.validated_data["code"].upper()
        plan_id = serializer.validated_data.get("plan_id", "")
        user_id = serializer.validated_data.get("user_id")

        try:
            promocode = Promocode.objects.get(code__iexact=code)
        except Promocode.DoesNotExist:
            return error_response(
                code="CODE_NOT_FOUND",
                message="Promocode not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        # Validate
        if not promocode.is_valid:
            return error_response(
                code="CODE_INVALID",
                message="Promocode is invalid or expired",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        # Check applicable plans
        if promocode.applicable_plans and plan_id and plan_id not in promocode.applicable_plans:
            return error_response(
                code="CODE_NOT_APPLICABLE",
                message="Promocode is not applicable to this plan",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        # Record usage
        from apps.users.models import User

        if user_id:
            try:
                user = User.objects.get(id=user_id)
                PromoCodeUsage.objects.create(
                    user=user,
                    code=code,
                    promocode=promocode,
                    discount_applied=promocode.discount_percent,
                )
            except User.DoesNotExist:
                pass

        # Increment usage count
        promocode.used_count += 1
        promocode.save()

        return success_response(
            data={
                "code": code,
                "discount_percent": promocode.discount_percent,
                "discount_amount": str(promocode.discount_amount)
                if promocode.discount_amount
                else None,
                "message": "Promocode applied successfully",
            },
            status_code=status.HTTP_200_OK,
        )


class PromoCodeUsageViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for promocode usage history."""

    queryset = PromoCodeUsage.objects.all()
    serializer_class = PromoCodeUsageSerializer
    permission_classes = [AllowAny]

    @action(detail=False, methods=["get"])
    def user_history(self, request):
        """Get a user's promocode usage history."""
        user_id = request.query_params.get("user_id")

        if not user_id:
            return error_response(
                code="MISSING_USER",
                message="user_id query parameter is required",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        usages = self.get_queryset().filter(user_id=user_id)
        serializer = self.get_serializer(usages, many=True)

        return success_response(data=serializer.data, status_code=status.HTTP_200_OK)
