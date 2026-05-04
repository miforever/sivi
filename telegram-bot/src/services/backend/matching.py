"""Job matching API."""

from typing import Any

from src.services.backend.base import _BackendClient


class MatchingAPI(_BackendClient):
    """API for resume-to-job matching."""

    async def find_matching_jobs(
        self,
        telegram_id: int,
        resume_id: str,
        limit: int = 20,
        filters: dict[str, Any] | None = None,
        exclude_ids: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Find jobs matching a resume via semantic search."""
        payload: dict[str, Any] = {
            "resume_id": resume_id,
            "limit": limit,
        }
        if filters:
            payload["filters"] = filters
        if exclude_ids:
            payload["exclude_ids"] = exclude_ids

        result = await self._handle_request(
            "POST",
            "/v1/matching/find-jobs/",
            telegram_id=telegram_id,
            json=payload,
            error_msg=f"Failed to find matching jobs for resume {resume_id}",
        )
        return result if isinstance(result, list) else []
