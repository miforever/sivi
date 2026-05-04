"""Subscription management API."""

import logging
from typing import Any

import httpx

from src.services.backend.base import _BackendClient

logger = logging.getLogger(__name__)


class SubscriptionAPI(_BackendClient):
    """API for subscription plans and lifecycle."""

    async def get_subscription_plans(self) -> list[dict[str, Any]]:
        """Get available subscription plans."""
        result = await self._handle_request(
            "GET",
            "/v1/subscriptions/plans/",
            error_msg="Failed to get subscription plans",
        )
        return result if isinstance(result, list) else []

    async def get_subscription_status(self, telegram_id: int) -> dict[str, Any]:
        """Get subscription status for a user."""
        return await self._handle_request(
            "GET",
            "/v1/subscriptions/status/",
            telegram_id=telegram_id,
            error_msg=f"Failed to get subscription status for telegram_id={telegram_id}",
        )

    async def subscription_activate(
        self,
        telegram_id: int,
        plan_id: str,
        payment_id: str = "",
    ) -> dict[str, Any]:
        """Activate a subscription for a user."""
        try:
            return await self._handle_request(
                "POST",
                "/v1/subscriptions/activate/",
                telegram_id=telegram_id,
                json={"plan_id": plan_id, "payment_id": payment_id},
                error_msg=(f"Failed to activate subscription for telegram_id={telegram_id}, plan_id={plan_id}"),
            )
        except httpx.HTTPStatusError as e:
            # Don't let this crash the bot
            logger.error(
                f"HTTP error activating subscription: {e.response.status_code} - "
                f"telegram_id={telegram_id}, plan_id={plan_id}"
            )
            return {
                "error": True,
                "status_code": e.response.status_code,
                "message": f"Backend returned {e.response.status_code}",
            }
        except Exception as e:
            logger.error(
                f"Unexpected error activating subscription: {e}",
                exc_info=True,
            )
            return {"error": True, "message": str(e)}

    async def subscription_renew(
        self,
        telegram_id: int,
        payment_id: str = "",
    ) -> dict[str, Any]:
        """Renew a user's current subscription."""
        return await self._handle_request(
            "POST",
            "/v1/subscriptions/renew/",
            telegram_id=telegram_id,
            json={"payment_id": payment_id},
            error_msg=f"Failed to renew subscription for telegram_id={telegram_id}",
        )

    async def subscription_cancel(self, telegram_id: int) -> dict[str, Any]:
        """Cancel a user's active subscription."""
        return await self._handle_request(
            "POST",
            "/v1/subscriptions/cancel/",
            telegram_id=telegram_id,
            error_msg=f"Failed to cancel subscription for telegram_id={telegram_id}",
        )
