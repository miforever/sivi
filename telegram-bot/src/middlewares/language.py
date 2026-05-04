"""Language middleware for the Sivi bot."""

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User

from src.services.container import ServiceContainer

logger = logging.getLogger(__name__)


class LanguageMiddleware(BaseMiddleware):
    """Middleware to inject user language into handlers from cache or backend."""

    def __init__(self, services: ServiceContainer):
        super().__init__()
        self.services = services

    async def get_user_language(self, user: User) -> str | None:
        user_data = await self.services.user_service.get_user(user.id)
        if not user_data:
            return None
        user_language = user_data.get("language")
        return user_language

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        """Process event and inject language from cache."""
        if event.from_user is None:
            return await handler(event, data)

        user_lang = None
        try:
            user_lang = await self.get_user_language(event.from_user)

        except Exception as e:
            logger.error("Language middleware error for user %s: %s", getattr(event.from_user, "id", "unknown"), str(e))

        data["user_lang"] = user_lang

        return await handler(event, data)
