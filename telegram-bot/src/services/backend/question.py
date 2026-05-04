"""Questions API."""

from typing import Any

from src.services.backend.base import _BackendClient


class QuestionAPI(_BackendClient):
    """API for retrieving resume creation questions."""

    async def get_questions(self, language: str, position: str) -> list[dict[str, Any]]:
        """Get the list of questions for resume creation."""
        result = await self._handle_request(
            "GET",
            f"/v1/questions/?language={language}&position={position}",
            error_msg=f"Failed to get questions for language {language} and position {position}",
        )
        return result if isinstance(result, list) else []
