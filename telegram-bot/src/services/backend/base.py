"""Base HTTP client for backend API communication."""

import logging
from contextlib import asynccontextmanager
from typing import Any

import httpx

from src.config import get_settings

logger = logging.getLogger(__name__)


class BackendServiceError(Exception):
    """Custom exception for backend service errors."""


class WeeklyLimitReachedError(BackendServiceError):
    """Raised when the user has exceeded their weekly AI call limit."""


class _BackendClient:
    """Base class with shared HTTP logic for all backend API clients."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.base_url = str(self.settings.BACKEND_URL).rstrip("/")
        self.api_key = self.settings.BACKEND_API_KEY
        self.timeout = self.settings.REQUEST_TIMEOUT

    @asynccontextmanager
    async def _get_client(self):
        """Get an HTTP client with proper configuration."""
        async with httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
        ) as client:
            yield client

    async def close(self):
        """Close the service (no-op for this implementation)."""

    def _get_headers(self, telegram_id: int | None = None) -> dict[str, str]:
        """Get request headers with API key and optional telegram ID."""
        headers = {"X-API-KEY": self.api_key}
        if telegram_id is not None:
            headers["X-Telegram-Id"] = str(telegram_id)
        return headers

    async def _request_json(
        self,
        method: str,
        endpoint: str,
        client: httpx.AsyncClient,
        telegram_id: int | None = None,
        **kwargs,
    ) -> dict:
        """Make a JSON request and return parsed response."""
        if "headers" not in kwargs:
            kwargs["headers"] = self._get_headers(telegram_id)

        response = await client.request(method, endpoint, **kwargs)
        response.raise_for_status()

        if not response.headers.get("content-type", "").startswith("application/json"):
            raise BackendServiceError("Expected JSON response")

        return response.json()

    async def _request_raw(
        self,
        method: str,
        endpoint: str,
        client: httpx.AsyncClient,
        telegram_id: int | None = None,
        **kwargs,
    ) -> httpx.Response:
        """Make a raw request and return response object."""
        if "headers" not in kwargs:
            kwargs["headers"] = self._get_headers(telegram_id)

        response = await client.request(method, endpoint, **kwargs)
        response.raise_for_status()
        return response

    async def _handle_request(
        self,
        method: str,
        endpoint: str,
        telegram_id: int | None = None,
        error_msg: str = "Request failed",
        return_data: bool = True,
        **kwargs,
    ) -> Any:
        """Generic request handler with error handling."""
        try:
            async with self._get_client() as client:
                response = await self._request_json(method, endpoint, client, telegram_id, **kwargs)
                return response.get("data", {} if return_data else None) if return_data else response
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 403:
                logger.info(f"User not found (403): {error_msg}")
                return {} if return_data else None

            # Check for weekly limit error from backend
            if e.response.status_code == 429:
                try:
                    body = e.response.json()
                    msg = body.get("error", {}).get("message", "Weekly limit reached")
                except Exception:
                    msg = "Weekly limit reached"
                raise WeeklyLimitReachedError(msg) from e

            # Log but DON'T raise - return error info instead
            logger.error(f"{error_msg}: {e.response.status_code} - {e.response.text}")

            # Return a structured error response
            return {
                "error": True,
                "status_code": e.response.status_code,
                "message": error_msg,
            }

        except BackendServiceError as e:
            logger.error(f"{error_msg}: {e}")
            return {} if return_data else None
        except Exception as e:
            logger.error(f"{error_msg}: Unexpected error - {e}", exc_info=True)
            return {"error": True, "message": str(e)}
