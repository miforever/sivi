"""User service for managing user data with caching."""

import logging
from typing import Any

from src.config import get_settings
from src.services.backend import BackendService, BackendServiceError
from src.services.cache import Cache, CacheError

logger = logging.getLogger(__name__)


class UserService:
    """Service for fetching and caching user data."""

    def __init__(self, cache: Cache, backend: BackendService):
        """
        Initialize the user service.

        Args:
            cache: Cache service instance
            backend: Backend service instance
        """
        self.cache = cache
        self.backend = backend
        self.settings = get_settings()

    async def get_user(self, telegram_id: int) -> dict[str, Any] | None:
        """
        Get user from cache or fetch from backend if not cached.

        Args:
            telegram_id: Telegram user ID

        Returns:
            dict: User data if found, None otherwise
        """
        # Try cache first
        try:
            cached_user = await self.cache.get_user(telegram_id)
            if cached_user:
                logger.debug("User %s found in cache", telegram_id)
                return cached_user
        except CacheError as e:
            logger.warning("Cache retrieval failed for user %s: %s", telegram_id, str(e))
            # Continue to backend call if cache fails

        # Cache miss - fetch from backend
        return await self._fetch_and_cache_user(telegram_id)

    async def _fetch_and_cache_user(self, telegram_id: int) -> dict[str, Any] | None:
        """
        Fetch user from backend and cache the result.

        Args:
            telegram_id: Telegram user ID

        Returns:
            dict: User data if found, None otherwise
        """
        try:
            # Fetch from backend
            user_data = await self.backend.user_get(telegram_id)

            if user_data:
                # Store in cache for next time
                try:
                    await self.cache.set_user(telegram_id, user_data)
                    logger.debug("Cached user %s from backend", telegram_id)
                except CacheError as e:
                    logger.warning("Failed to cache user %s: %s", telegram_id, str(e))
                    # Don't fail if caching fails - we still have the data

                return user_data

            logger.debug("User %s not found in backend", telegram_id)
            return None

        except BackendServiceError as e:
            logger.error("Backend error fetching user %s: %s", telegram_id, str(e))
            return None

    async def create_user(self, user_data: dict[str, Any]) -> dict[str, Any] | None:
        """
        Create a new user in backend and cache.

        Args:
            user_data: User data to create (must include telegram_id)

        Returns:
            dict: Created user data if successful, None otherwise
        """
        telegram_id = user_data.get("telegram_id")
        if not telegram_id:
            logger.error("Cannot create user without telegram_id")
            return None

        try:
            # Create in backend
            created_user = await self.backend.user_register(user_data)

            if created_user:
                # Cache the created user
                try:
                    await self.cache.set_user(telegram_id, created_user)
                    logger.debug("Cached newly created user %s", telegram_id)
                except CacheError as e:
                    logger.warning("Failed to cache created user %s: %s", telegram_id, str(e))

                return created_user

            logger.error("Failed to create user %s in backend", telegram_id)
            return None

        except BackendServiceError as e:
            logger.error("Backend error creating user %s: %s", telegram_id, str(e))
            return None

    async def update_user(self, telegram_id: int, user_data: dict[str, Any]) -> dict[str, Any] | None:
        """
        Update user in backend and invalidate cache.

        Args:
            telegram_id: Telegram user ID
            user_data: User data to update

        Returns:
            dict: Updated user data if successful, None otherwise
        """
        try:
            # Update in backend
            updated_user = await self.backend.user_update(telegram_id, user_data)

            if updated_user:
                # Update cache with fresh data
                try:
                    await self.cache.set_user(telegram_id, updated_user)
                    logger.debug("Updated cache for user %s", telegram_id)
                except CacheError as e:
                    logger.warning("Failed to update cache for user %s: %s", telegram_id, str(e))

                return updated_user

            logger.error("Failed to update user %s in backend", telegram_id)
            return None

        except BackendServiceError as e:
            logger.error("Backend error updating user %s: %s", telegram_id, str(e))
            return None

    async def refresh_user(self, telegram_id: int) -> dict[str, Any] | None:
        """
        Force refresh user data from backend, bypassing cache.
        Useful after profile updates.

        Args:
            telegram_id: Telegram user ID

        Returns:
            dict: Fresh user data if found, None otherwise
        """
        # Invalidate cache first
        await self.invalidate_cache(telegram_id)

        # Fetch fresh data
        return await self._fetch_and_cache_user(telegram_id)

    async def invalidate_cache(self, telegram_id: int) -> None:
        """
        Invalidate user cache (call after user updates their profile).

        Args:
            telegram_id: Telegram user ID
        """
        try:
            await self.cache.delete_user(telegram_id)
            logger.debug("Invalidated cache for user %s", telegram_id)
        except CacheError as e:
            logger.warning("Failed to invalidate cache for user %s: %s", telegram_id, str(e))

    async def close(self):
        """Close all service connections."""
        await self.backend.close()
        await self.cache.close()
