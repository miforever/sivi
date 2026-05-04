"""User views."""

from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from apps.common.authentication import ApiKeyAuthentication, TelegramBotAuthentication
from apps.common.permissions import IsUserOrAdmin
from apps.common.responses import error_response, success_response
from apps.users.models import User
from apps.users.serializers import (
    UserCreateSerializer,
    UserSerializer,
    UserUpdateSerializer,
)


class TelegramUserViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """
    ViewSet for Telegram bot user management.
    Only supports user creation with API key authentication.
    """

    queryset = User.objects.all()
    serializer_class = UserCreateSerializer
    authentication_classes = [ApiKeyAuthentication]
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        """Create a new user from Telegram bot."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return success_response(data=UserSerializer(user).data, status_code=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get", "patch", "delete"], permission_classes=[AllowAny])
    def me(self, request):
        """
        Get, update, or delete the current user.
        Works for both Telegram bot and JWT clients.
        """
        user = None

        # Telegram bot flow
        telegram_id = request.META.get("HTTP_X_TELEGRAM_ID")
        if telegram_id:
            try:
                user = User.objects.get(telegram_id=telegram_id)
            except User.DoesNotExist:
                return error_response(
                    code="USER_NOT_FOUND",
                    message="User with this Telegram ID does not exist.",
                    status_code=status.HTTP_404_NOT_FOUND,
                )

        # JWT/web/app flow
        elif request.user and request.user.is_authenticated:
            user = request.user

        if not user:
            return error_response(
                code="USER_NOT_FOUND",
                message="User not found.",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        if request.method == "GET":
            serializer = UserSerializer(user)
            return success_response(data=serializer.data, status_code=200)

        elif request.method == "PATCH":
            serializer = UserUpdateSerializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return success_response(data=UserSerializer(user).data, status_code=200)

        elif request.method == "DELETE":
            user.delete()
            return success_response(data={}, status_code=204)


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for User model.
    Supports both Telegram bot (API key + telegram_id) and Web/App (JWT) authentication.
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer

    authentication_classes = [TelegramBotAuthentication, JWTAuthentication]

    def get_permissions(self):
        """
        Set permissions based on action.
        """
        if self.action == "create":
            return [AllowAny()]
        if self.action in ["update", "partial_update", "destroy"]:
            return [IsAuthenticated(), IsUserOrAdmin()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == "create":
            return UserCreateSerializer
        if self.action in ["update", "partial_update", "me"]:
            return UserUpdateSerializer
        return UserSerializer
