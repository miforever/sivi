"""Throttling middleware for the Sivi bot."""

import asyncio
import time
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from src.services.container import ServiceContainer


class ThrottlingMiddleware(BaseMiddleware):
    """Middleware to throttle user requests."""

    def __init__(self, services: ServiceContainer, rate_limit: float = 0.3):
        super().__init__()
        self.cache = services.cache
        self.rate_limit = rate_limit  # seconds between requests

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        # --- Identify the user ---
        if isinstance(event, Message):
            user_id = event.from_user.id if event.from_user else None
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id if event.from_user else None
        else:
            # No user identified, skip throttling
            return await handler(event, data)

        if user_id is None:
            return await handler(event, data)

        now_ts = time.time()
        throttle_key = f"throttle:last:{user_id}"
        warn_key = f"throttle:warned:{user_id}"

        try:
            # --- Check last request time with timeout ---
            last_request = await asyncio.wait_for(self.cache.redis.get(throttle_key), timeout=1.0)
        except TimeoutError:
            # If Redis is slow, allow the request through
            return await handler(event, data)

        # --- Check if user is sending requests too fast ---
        if last_request:
            last_request_time = float(last_request)
            time_since_last = now_ts - last_request_time

            if time_since_last < self.rate_limit:
                # User is being throttled

                # Send warning only once during cooldown period
                try:
                    already_warned = await asyncio.wait_for(self.cache.redis.get(warn_key), timeout=1.0)

                    if not already_warned:
                        _ = data.get("_")
                        if not _:
                            from src.utils.i18n import get_function

                            _ = get_function("uz")

                        if isinstance(event, Message):
                            await event.answer(_("throttle_message"))
                        elif isinstance(event, CallbackQuery):
                            await event.answer(_("throttle_callback"), show_alert=True)

                        # Mark as warned for the cooldown period
                        await self.cache.redis.set(
                            warn_key,
                            "1",
                            ex=max(1, int(self.rate_limit * 2)),  # Warning expires after 2x rate limit
                        )
                except (TimeoutError, Exception):
                    # If warning fails, continue silently
                    pass

                # Don't process the request - return True to indicate handled
                return True

        # --- Request is allowed, update last request time ---
        try:
            await asyncio.wait_for(
                self.cache.redis.set(
                    throttle_key,
                    str(now_ts),
                    ex=max(1, int(self.rate_limit * 5)),  # Keep tracking for 5x rate limit
                ),
                timeout=1.0,
            )
        except TimeoutError:
            # If Redis set fails, still process the request
            pass

        # --- Process the event ---
        return await handler(event, data)
