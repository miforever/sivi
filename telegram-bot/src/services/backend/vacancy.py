"""Vacancy search API."""

from typing import Any

from src.services.backend.base import _BackendClient


class VacancyAPI(_BackendClient):
    """API for vacancy search and retrieval."""

    async def get_vacancy(self, vacancy_id: str) -> dict[str, Any] | None:
        """Get vacancy details by ID."""
        return await self._handle_request(
            "GET",
            f"/v1/user/vacancies/{vacancy_id}/",
            error_msg=f"Failed to get vacancy {vacancy_id}",
        )
