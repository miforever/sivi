"""Event tracking API."""

from typing import Any

from src.services.backend.base import _BackendClient


class EventAPI(_BackendClient):
    """API for tracking user events."""

    async def track_event(
        self,
        telegram_id: int,
        event_type: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Fire-and-forget event tracking."""
        await self._handle_request(
            "POST",
            "/v1/analytics/track-event/",
            telegram_id=telegram_id,
            json={
                "event_type": event_type,
                "telegram_id": telegram_id,
                "metadata": metadata or {},
            },
            error_msg=f"Failed to track event {event_type}",
            return_data=False,
        )
