"""Custom authentication classes."""

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from drf_spectacular.extensions import OpenApiAuthenticationExtension
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from apps.users.models import User


class ApiKeyAuthentication(BaseAuthentication):
    def authenticate(self, request):
        api_key = request.META.get("HTTP_X_API_KEY")

        if not api_key:
            return None

        if api_key not in settings.API_KEYS:
            raise AuthenticationFailed("Invalid API key")

        return (AnonymousUser(), api_key)


class TelegramBotAuthentication(BaseAuthentication):
    """
    Authenticate requests from Telegram bot using API key + telegram_id.
    Returns the actual User object based on telegram_id.
    """

    def authenticate(self, request):
        api_key = request.META.get("HTTP_X_API_KEY")
        telegram_id = request.META.get("HTTP_X_TELEGRAM_ID")

        # Skip if neither header is present (let other authenticators handle it)
        if not api_key and not telegram_id:
            return None

        # Validate API key
        if not api_key or api_key not in settings.API_KEYS:
            raise AuthenticationFailed("Invalid API key")

        # Find user by telegram_id
        if not telegram_id:
            return None
        try:
            user = User.objects.get(telegram_id=telegram_id)
            return (user, None)  # Return actual user object
        except User.DoesNotExist:
            raise AuthenticationFailed("User with this Telegram ID does not exist.")


class TelegramBotAuthenticationScheme(OpenApiAuthenticationExtension):
    """
    OpenAPI schema extension for TelegramBotAuthentication.
    This tells drf-spectacular how to document the authentication in Swagger.
    """

    target_class = "apps.common.authentication.TelegramBotAuthentication"
    name = "TelegramBotAuth"

    def get_security_definition(self, auto_schema):
        return {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-KEY",
            "description": "Telegram Bot Authentication requires two headers: X-API-KEY and X-Telegram-Id",
        }
