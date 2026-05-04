"""Logging middleware for the Sivi bot."""

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseMiddleware):
    """Middleware to log user interactions."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        # Log the incoming event
        if isinstance(event, Message):
            user_id = event.from_user.id if event.from_user else "Unknown"
            username = event.from_user.username if event.from_user else "Unknown"
            logger.info(
                "Message from user %s (@%s): %s",
                user_id,
                username,
                event.text[:50] + "..." if event.text and len(event.text) > 50 else event.text,
            )
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id if event.from_user else "Unknown"
            username = event.from_user.username if event.from_user else "Unknown"
            logger.info("Callback from user %s (@%s): %s", user_id, username, event.data)

        # Call the handler
        result = await handler(event, data)

        # Log the result
        if isinstance(event, Message):
            user_id = event.from_user.id if event.from_user else "Unknown"
            logger.debug("Message handled for user %s", user_id)
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id if event.from_user else "Unknown"
            logger.debug("Callback handled for user %s", user_id)

        return result
