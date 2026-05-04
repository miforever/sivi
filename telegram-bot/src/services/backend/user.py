"""User management API."""

import logging
from typing import Any

import httpx

from src.services.backend.base import _BackendClient

logger = logging.getLogger(__name__)


class UserAPI(_BackendClient):
    """API for user registration and management."""

    async def user_register(self, user_data: dict) -> dict[str, Any]:
        """Register a new user."""
        return await self._handle_request(
            "POST",
            "/v1/user/telegram/",
            json=user_data,
            error_msg=f"Failed to create user {user_data.get('telegram_id')}",
        )

    async def user_update(self, telegram_id: int, user_data: dict) -> dict[str, Any]:
        """Update user information."""
        return await self._handle_request(
            "PATCH",
            "/v1/user/telegram/me/",
            telegram_id=telegram_id,
            json=user_data,
            error_msg=f"Failed to update user {telegram_id}",
        )

    async def user_get(self, telegram_id: int) -> dict[str, Any]:
        """Get user information.

        Returns empty dict if user not found (404).
        """
        try:
            async with self._get_client() as client:
                response = await self._request_json(
                    "GET",
                    "/v1/user/telegram/me/",
                    client,
                    telegram_id=telegram_id,
                )
                return response.get("data", {})
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.info(f"User {telegram_id} not found")
                return {}
            logger.error(f"Failed to get user {telegram_id}: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Failed to get user {telegram_id}: {e}")
            raise
