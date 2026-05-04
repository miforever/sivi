"""Middleware to inject services into handlers."""

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from src.services.container import ServiceContainer


class ServicesMiddleware(BaseMiddleware):
    """Middleware to inject service container into handlers."""

    def __init__(self, services: ServiceContainer):
        self.services = services

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        # Inject services into handler data
        data["services"] = self.services
        return await handler(event, data)
