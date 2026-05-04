"""Redis cache service for storing user state and temporary data."""

import json
import logging
from typing import Any

import redis.asyncio as redis
from redis.exceptions import RedisError

from src.config import get_settings

logger = logging.getLogger(__name__)


class CacheError(Exception):
    """Custom exception for cache service errors."""

    pass


class Cache:
    """Redis cache service for the Sivi bot."""

    def __init__(self, redis_client: redis.Redis | None = None):
        """
        Initialize the cache service.

        Args:
            redis_client: Optional Redis client instance. If not provided, a new one will be created.
        """
        self.settings = get_settings()
        self.redis = redis_client or self._create_redis_client()

    def _create_redis_client(self) -> redis.Redis:
        """Create and return a Redis client instance."""
        try:
            return redis.Redis.from_url(str(self.settings.REDIS_URL), decode_responses=True, encoding="utf-8")
        except Exception as e:
            logger.error("Failed to create Redis client: %s", str(e))
            raise CacheError(f"Redis connection failed: {e!s}")

    async def close(self):
        """Close the Redis connection."""
        try:
            await self.redis.close()
        except Exception as e:
            logger.error("Error closing Redis connection: %s", str(e))

    def _get_user_key(self, user_id: int, key: str) -> str:
        """Generate a Redis key for user-specific data."""
        return f"user:{user_id}:{key}"

    async def _safe_operation(self, operation, *args, **kwargs):
        """Safely execute a Redis operation with error handling."""
        try:
            return await operation(*args, **kwargs)
        except RedisError as e:
            logger.error("Redis operation failed: %s", str(e))
            raise CacheError(f"Redis operation failed: {e!s}")
        except Exception as e:
            logger.error("Unexpected cache error: %s", str(e))
            raise CacheError(f"Unexpected error: {e!s}")

    # ==================== User Profile Caching ====================

    async def set_user(self, user_id: int, user_data: dict[str, Any]) -> None:
        """Store user data in cache."""
        if not isinstance(user_data, dict):
            raise ValueError("User data must be a dictionary")

        key = self._get_user_key(user_id, "profile")
        serialized_user = json.dumps(user_data, ensure_ascii=False)

        await self._safe_operation(self.redis.set, key, serialized_user, ex=self.settings.USER_CACHE_TTL)
        logger.debug("Cached user data for user %s", user_id)

    async def get_user(self, user_id: int) -> dict[str, Any] | None:
        """Retrieve user data from cache."""
        key = self._get_user_key(user_id, "profile")
        user_data = await self._safe_operation(self.redis.get, key)

        if user_data:
            try:
                parsed_user = json.loads(user_data)
                logger.debug("Retrieved user data from cache for user %s", user_id)
                return parsed_user
            except json.JSONDecodeError as e:
                logger.error("Failed to parse user data for user %s: %s", user_id, str(e))
                return None
        return None

    async def delete_user(self, user_id: int) -> None:
        """Remove user data from cache."""
        key = self._get_user_key(user_id, "profile")
        await self._safe_operation(self.redis.delete, key)
        logger.debug("Deleted user cache for user %s", user_id)

    # ==================== Resume Answers (Temporary Form Data) ====================

    async def set_resume_answers(self, user_id: int, answers: dict[str, Any], ttl: int | None = None) -> None:
        """Store user's resume answers."""
        if not isinstance(answers, dict):
            raise ValueError("Answers must be a dictionary")

        if ttl is None:
            ttl = self.settings.RESUME_ANSWERS_TTL

        key = self._get_user_key(user_id, "resume:answers")
        serialized_answers = json.dumps(answers, ensure_ascii=False)

        await self._safe_operation(self.redis.set, key, serialized_answers, ex=ttl)
        logger.debug("Set resume answers for user %s", user_id)

    async def get_resume_answers(self, user_id: int) -> dict[str, Any]:
        """Retrieve user's resume answers."""
        key = self._get_user_key(user_id, "resume:answers")
        answers = await self._safe_operation(self.redis.get, key)

        if answers:
            try:
                parsed_answers = json.loads(answers)
                logger.debug("Retrieved resume answers for user %s", user_id)
                return parsed_answers
            except json.JSONDecodeError as e:
                logger.error("Failed to parse resume answers for user %s: %s", user_id, str(e))
                return {}
        return {}

    async def clear_resume_answers(self, user_id: int) -> None:
        """Clear user's resume answers."""
        key = self._get_user_key(user_id, "resume:answers")
        await self._safe_operation(self.redis.delete, key)
        logger.debug("Cleared resume answers for user %s", user_id)

    # ==================== User State Management ====================

    async def set_user_state(self, user_id: int, state: str, data: dict[str, Any] | None = None) -> None:
        """Set user's state with optional data."""
        if not state or not isinstance(state, str):
            raise ValueError("State must be a non-empty string")

        key = self._get_user_key(user_id, "state")
        value = {"state": state}
        if data:
            if not isinstance(data, dict):
                raise ValueError("Data must be a dictionary")
            value["data"] = data

        serialized_value = json.dumps(value, ensure_ascii=False)
        await self._safe_operation(
            self.redis.set,
            key,
            serialized_value,
            ex=86400,  # 1 day TTL for state
        )
        logger.debug("Set state for user %s: %s", user_id, state)

    async def get_user_state(self, user_id: int) -> dict[str, Any]:
        """Get user's current state and data."""
        key = self._get_user_key(user_id, "state")
        state_data = await self._safe_operation(self.redis.get, key)

        if state_data:
            try:
                parsed_state = json.loads(state_data)
                return parsed_state
            except json.JSONDecodeError as e:
                logger.error("Failed to parse user state for user %s: %s", user_id, str(e))
                return {"state": None, "data": {}}
        return {"state": None, "data": {}}

    async def clear_user_state(self, user_id: int) -> None:
        """Clear user's state."""
        key = self._get_user_key(user_id, "state")
        await self._safe_operation(self.redis.delete, key)
        logger.debug("Cleared state for user %s", user_id)

    # ==================== Resumes Caching ====================

    async def get_user_resumes(self, user_id: int) -> list[dict[str, Any]]:
        """Get user's resumes."""
        key = self._get_user_key(user_id, "resumes")
        resumes = await self._safe_operation(self.redis.get, key)

        if resumes:
            try:
                parsed_resumes = json.loads(resumes)
                logger.debug("Retrieved resumes for user %s", user_id)
                return parsed_resumes
            except json.JSONDecodeError as e:
                logger.error("Failed to parse resumes for user %s: %s", user_id, str(e))
                return []
        return []

    async def get_user_resume(self, user_id: int, resume_id: int) -> dict[str, Any] | None:
        """Get a specific resume for a user by ID."""
        resumes = await self.get_user_resumes(user_id)

        for resume in resumes:
            if resume.get("id") == resume_id:
                logger.debug("Retrieved resume %d for user %s", resume_id, user_id)
                return resume

        logger.debug("Resume %d not found for user %s", resume_id, user_id)
        return None

    async def save_user_resumes(self, user_id: int, resumes: list[dict[str, Any]]) -> None:
        """Save user's resumes."""
        key = self._get_user_key(user_id, "resumes")
        serialized_resumes = json.dumps(resumes, ensure_ascii=False)
        await self._safe_operation(self.redis.set, key, serialized_resumes, ex=self.settings.RESUMES_CACHE_TTL)
        logger.debug("Saved resumes for user %s", user_id)

    # ==================== Credits Caching ====================

    async def get_credit_packages(self) -> list[dict[str, Any]]:
        """
        Get credit packages from cache.

        Returns:
            List of credit package dictionaries
        """
        key = "credit:packages"
        packages = await self._safe_operation(self.redis.get, key)

        if packages:
            try:
                parsed_packages = json.loads(packages)
                logger.debug("Retrieved credit packages from cache")
                return parsed_packages
            except json.JSONDecodeError as e:
                logger.error("Failed to parse credit packages: %s", str(e))
                return []
        return []

    async def set_credit_packages(self, packages: list[dict[str, Any]], ttl: int | None = None) -> None:
        """
        Cache credit packages.

        Args:
            packages: List of credit package dictionaries
            ttl: Optional TTL in seconds (defaults to 1 hour)
        """
        if not isinstance(packages, list):
            raise ValueError("Packages must be a list")

        if ttl is None:
            ttl = 3600  # 1 hour default

        key = "credit:packages"
        serialized_packages = json.dumps(packages, ensure_ascii=False)

        await self._safe_operation(self.redis.set, key, serialized_packages, ex=ttl)
        logger.debug("Cached credit packages")

    async def get_user_credits(self, user_id: int) -> dict[str, Any] | None:
        """
        Get user's credit balance and statistics from cache.

        Returns:
            Dict with current_balance and statistics, or None if not cached
        """
        key = self._get_user_key(user_id, "credits")
        credits_data = await self._safe_operation(self.redis.get, key)

        if credits_data:
            try:
                parsed_credits = json.loads(credits_data)
                logger.debug("Retrieved credits from cache for user %s", user_id)
                return parsed_credits
            except json.JSONDecodeError as e:
                logger.error("Failed to parse credits for user %s: %s", user_id, str(e))
                return None
        return None

    async def set_user_credits(self, user_id: int, credits_data: dict[str, Any], ttl: int | None = None) -> None:
        """
        Cache user's credit balance and statistics.

        Args:
            user_id: Telegram user ID
            credits_data: Credit data (current_balance, statistics)
            ttl: Optional TTL in seconds (defaults to 5 minutes)
        """
        if not isinstance(credits_data, dict):
            raise ValueError("Credits data must be a dictionary")

        if ttl is None:
            ttl = 300  # 5 minutes default

        key = self._get_user_key(user_id, "credits")
        serialized_credits = json.dumps(credits_data, ensure_ascii=False)

        await self._safe_operation(self.redis.set, key, serialized_credits, ex=ttl)
        logger.debug("Cached credits for user %s", user_id)

    async def delete_user_credits(self, user_id: int) -> None:
        """
        Remove user's credits from cache.
        Should be called after credit purchases or consumption.
        """
        key = self._get_user_key(user_id, "credits")
        await self._safe_operation(self.redis.delete, key)
        logger.debug("Deleted credits cache for user %s", user_id)

    # ==================== Subscription Plans Caching ====================

    async def get_subscription_plans(self) -> list[dict[str, Any]]:
        """Get subscription plans from cache."""
        key = "subscription:plans"
        plans = await self._safe_operation(self.redis.get, key)

        if plans:
            try:
                parsed_plans = json.loads(plans)
                logger.debug("Retrieved subscription plans from cache")
                return parsed_plans
            except json.JSONDecodeError as e:
                logger.error("Failed to parse subscription plans: %s", str(e))
                return []
        return []

    async def set_subscription_plans(self, plans: list[dict[str, Any]], ttl: int | None = None) -> None:
        """Cache subscription plans."""
        if not isinstance(plans, list):
            raise ValueError("Plans must be a list")

        if ttl is None:
            ttl = 3600  # 1 hour default for plans

        key = "subscription:plans"
        serialized_plans = json.dumps(plans, ensure_ascii=False)

        await self._safe_operation(self.redis.set, key, serialized_plans, ex=ttl)
        logger.debug("Cached subscription plans")

    # ==================== User Subscription Status Caching ====================

    async def get_user_subscription(self, user_id: int) -> dict[str, Any] | None:
        """Get user's subscription status from cache."""
        key = self._get_user_key(user_id, "subscription")
        subscription = await self._safe_operation(self.redis.get, key)

        if subscription:
            try:
                parsed_subscription = json.loads(subscription)
                logger.debug("Retrieved subscription status from cache for user %s", user_id)
                return parsed_subscription
            except json.JSONDecodeError as e:
                logger.error("Failed to parse subscription for user %s: %s", user_id, str(e))
                return None
        return None

    async def set_user_subscription(
        self, user_id: int, subscription_data: dict[str, Any], ttl: int | None = None
    ) -> None:
        """Cache user's subscription status."""
        if not isinstance(subscription_data, dict):
            raise ValueError("Subscription data must be a dictionary")

        if ttl is None:
            ttl = 300  # 5 minutes default for subscription status

        key = self._get_user_key(user_id, "subscription")
        serialized_subscription = json.dumps(subscription_data, ensure_ascii=False)

        await self._safe_operation(self.redis.set, key, serialized_subscription, ex=ttl)
        logger.debug("Cached subscription status for user %s", user_id)

    async def delete_user_subscription(self, user_id: int) -> None:
        """Remove user's subscription from cache."""
        key = self._get_user_key(user_id, "subscription")
        await self._safe_operation(self.redis.delete, key)
        logger.debug("Deleted subscription cache for user %s", user_id)

    # ==================== Health Check ====================

    async def ping(self) -> bool:
        """Test Redis connection."""
        try:
            await self._safe_operation(self.redis.ping)
            return True
        except CacheError:
            return False
