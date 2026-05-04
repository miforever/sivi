"""Credit management API."""

import logging
from typing import Any

import httpx

from src.services.backend.base import _BackendClient

logger = logging.getLogger(__name__)


class CreditAPI(_BackendClient):
    """API for credit packages, purchases, and balance."""

    async def get_credit_packages(self, telegram_id: int) -> list[dict[str, Any]]:
        """Get available credit packages for purchase.

        Returns:
            List of credit packages with pricing info
        """
        result = await self._handle_request(
            "GET",
            "/v1/resumes/credit-packages/",
            telegram_id=telegram_id,
            error_msg="Failed to get credit packages",
        )
        return result if isinstance(result, list) else []

    async def purchase_credits(
        self,
        telegram_id: int,
        credits: int,
        payment_id: str,
        payment_provider: str = "click",
        amount_paid: float | None = None,
        currency: str = "UZS",
    ) -> dict[str, Any]:
        """Process credit purchase after successful payment.

        Args:
            telegram_id: Telegram user ID
            credits: Number of credits purchased
            payment_id: Payment transaction ID
            payment_provider: Payment provider name
            amount_paid: Amount paid (optional)
            currency: Currency code

        Returns:
            Response dict with success status and new balance
        """
        payload = {
            "credits": credits,
            "payment_id": payment_id,
            "payment_provider": payment_provider,
            "telegram_user_id": telegram_id,
        }

        if amount_paid is not None:
            payload["amount_paid"] = amount_paid
        if currency:
            payload["currency"] = currency

        try:
            async with self._get_client() as client:
                response = await self._request_json(
                    "POST",
                    "/v1/resumes/purchase-credits/",
                    client,
                    telegram_id=telegram_id,
                    json=payload,
                )

                logger.info(f"Credits purchased: telegram_id={telegram_id}, credits={credits}, payment_id={payment_id}")

                return {
                    "success": True,
                    "data": response.get("data", {}),
                    "message": response.get("message", ""),
                }

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 409:
                logger.warning(f"Payment already processed: telegram_id={telegram_id}, payment_id={payment_id}")
                return {
                    "success": False,
                    "error": "PAYMENT_ALREADY_PROCESSED",
                    "message": "This payment has already been processed",
                }

            try:
                error_data = e.response.json()
            except Exception:
                error_data = {"message": e.response.text}

            logger.error(f"Failed to purchase credits: status={e.response.status_code}, error={error_data}")
            return {
                "success": False,
                "error": error_data.get("code", "UNKNOWN_ERROR"),
                "message": error_data.get("message", "Failed to purchase credits"),
            }

        except Exception as e:
            logger.error(f"Unexpected error purchasing credits: {e}", exc_info=True)
            return {
                "success": False,
                "error": "UNEXPECTED_ERROR",
                "message": f"Unexpected error: {e!s}",
            }

    async def get_user_credits(self, telegram_id: int) -> dict[str, Any]:
        """Get user's credit balance and statistics.

        Returns:
            Dict with current_balance and statistics
        """
        return await self._handle_request(
            "GET",
            "/v1/resumes/credits/",
            telegram_id=telegram_id,
            error_msg=f"Failed to get credits for user {telegram_id}",
        )

    async def get_credit_history(
        self,
        telegram_id: int,
        transaction_type: str | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        """Get user's credit transaction history.

        Args:
            telegram_id: Telegram user ID
            transaction_type: Filter by type (purchase, usage, refund)
            limit: Number of records (default: 50, max: 200)

        Returns:
            Dict with transactions list and count
        """
        params: dict[str, Any] = {"limit": min(limit, 200)}
        if transaction_type:
            params["type"] = transaction_type

        return await self._handle_request(
            "GET",
            "/v1/resumes/credit-history/",
            telegram_id=telegram_id,
            params=params,
            error_msg=f"Failed to get credit history for user {telegram_id}",
        )
