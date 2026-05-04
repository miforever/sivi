"""User service for managing user data with caching."""

import logging
from typing import Any

from src.services.backend import BackendService, BackendServiceError
from src.services.cache import Cache, CacheError

logger = logging.getLogger(__name__)


class SubscriptionService:
    """Service for managing subscription plans and user subscriptions."""

    def __init__(self, cache: Cache, backend: BackendService):
        """
        Initialize the subscription service.

        Args:
            cache: Cache service instance
            backend: Backend service instance
        """
        self.cache = cache
        self.backend = backend

    async def get_plans(self) -> list[dict[str, Any]]:
        """
        Get subscription plans from cache or fetch from backend.

        Returns:
            list: List of subscription plan dictionaries
        """
        # Try cache first
        try:
            cached_plans = await self.cache.get_subscription_plans()
            if cached_plans:
                logger.debug("Subscription plans found in cache")
                return cached_plans
        except CacheError as e:
            logger.warning("Cache retrieval failed for subscription plans: %s", str(e))

        # Cache miss - fetch from backend
        return await self._fetch_and_cache_plans()

    async def _fetch_and_cache_plans(self) -> list[dict[str, Any]]:
        """
        Fetch plans from backend and cache them.

        Returns:
            list: List of subscription plan dictionaries
        """
        try:
            plans = await self.backend.get_subscription_plans()

            if plans:
                # Cache the plans
                try:
                    await self.cache.set_subscription_plans(plans)
                    logger.debug("Cached subscription plans from backend")
                except CacheError as e:
                    logger.warning("Failed to cache subscription plans: %s", str(e))

            return plans

        except BackendServiceError as e:
            logger.error("Backend error fetching subscription plans: %s", str(e))
            return []

    async def get_user_subscription(self, telegram_id: int) -> dict[str, Any]:
        """
        Get user's subscription status from cache or backend.

        Args:
            telegram_id: Telegram user ID

        Returns:
            dict: Subscription status data (empty dict if no subscription)
        """
        # Try cache first
        try:
            cached_subscription = await self.cache.get_user_subscription(telegram_id)
            if cached_subscription is not None:
                logger.debug("Subscription status found in cache for user %s", telegram_id)
                return cached_subscription
        except CacheError as e:
            logger.warning("Cache retrieval failed for user %s subscription: %s", telegram_id, str(e))

        # Cache miss - fetch from backend
        return await self._fetch_and_cache_subscription(telegram_id)

    async def _fetch_and_cache_subscription(self, telegram_id: int) -> dict[str, Any]:
        """
        Fetch subscription from backend and cache it.

        Args:
            telegram_id: Telegram user ID

        Returns:
            dict: Subscription status data
        """
        try:
            subscription = await self.backend.get_subscription_status(telegram_id)

            if subscription:
                # Cache the subscription status
                try:
                    await self.cache.set_user_subscription(telegram_id, subscription)
                    logger.debug("Cached subscription status for user %s", telegram_id)
                except CacheError as e:
                    logger.warning("Failed to cache subscription for user %s: %s", telegram_id, str(e))

            return subscription

        except BackendServiceError as e:
            logger.error("Backend error fetching subscription for user %s: %s", telegram_id, str(e))
            return {}

    async def activate_subscription(
        self, telegram_id: int, plan_id: str, payment_id: str = ""
    ) -> dict[str, Any] | None:
        """
        Activate a subscription for a user.

        Args:
            telegram_id: Telegram user ID
            plan_id: Subscription plan identifier
            payment_id: Payment transaction ID

        Returns:
            dict: Activated subscription data if successful, None otherwise
        """
        try:
            subscription = await self.backend.subscription_activate(telegram_id, plan_id, payment_id)

            if subscription:
                # Invalidate cache and update with new subscription
                await self.invalidate_subscription_cache(telegram_id)

                try:
                    await self.cache.set_user_subscription(telegram_id, subscription)
                    logger.debug("Cached activated subscription for user %s", telegram_id)
                except CacheError as e:
                    logger.warning("Failed to cache activated subscription: %s", str(e))

                return subscription

            return None

        except BackendServiceError as e:
            logger.error("Backend error activating subscription: %s", str(e))
            return None

    async def renew_subscription(self, telegram_id: int, payment_id: str = "") -> dict[str, Any] | None:
        """
        Renew a user's subscription.

        Args:
            telegram_id: Telegram user ID
            payment_id: Payment transaction ID

        Returns:
            dict: Renewed subscription data if successful, None otherwise
        """
        try:
            subscription = await self.backend.subscription_renew(telegram_id, payment_id)

            if subscription:
                # Invalidate cache and update
                await self.invalidate_subscription_cache(telegram_id)

                try:
                    await self.cache.set_user_subscription(telegram_id, subscription)
                    logger.debug("Cached renewed subscription for user %s", telegram_id)
                except CacheError as e:
                    logger.warning("Failed to cache renewed subscription: %s", str(e))

                return subscription

            return None

        except BackendServiceError as e:
            logger.error("Backend error renewing subscription: %s", str(e))
            return None

    async def cancel_subscription(self, telegram_id: int) -> dict[str, Any] | None:
        """
        Cancel a user's subscription.

        Args:
            telegram_id: Telegram user ID

        Returns:
            dict: Cancelled subscription data if successful, None otherwise
        """
        try:
            subscription = await self.backend.subscription_cancel(telegram_id)

            if subscription:
                # Invalidate cache
                await self.invalidate_subscription_cache(telegram_id)

                return subscription

            return None

        except BackendServiceError as e:
            logger.error("Backend error cancelling subscription: %s", str(e))
            return None

    async def invalidate_subscription_cache(self, telegram_id: int) -> None:
        """
        Invalidate subscription cache for a user.
        Call after subscription changes.

        Args:
            telegram_id: Telegram user ID
        """
        try:
            await self.cache.delete_user_subscription(telegram_id)
            logger.debug("Invalidated subscription cache for user %s", telegram_id)
        except CacheError as e:
            logger.warning("Failed to invalidate subscription cache: %s", str(e))

    async def refresh_subscription(self, telegram_id: int) -> dict[str, Any]:
        """
        Force refresh subscription data from backend.

        Args:
            telegram_id: Telegram user ID

        Returns:
            dict: Fresh subscription data
        """
        await self.invalidate_subscription_cache(telegram_id)
        return await self._fetch_and_cache_subscription(telegram_id)
