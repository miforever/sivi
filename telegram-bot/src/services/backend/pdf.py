"""PDF generation and export API."""

import logging
from typing import Any

from src.services.backend.base import _BackendClient

logger = logging.getLogger(__name__)


class PDFAPI(_BackendClient):
    """API for PDF generation and export."""

    async def generate_pdf_from_resume(
        self,
        telegram_id: int,
        resume_data: dict[str, Any],
        profile_image: str | None = None,
        language: str | None = None,
    ) -> bytes | None:
        """Generate a PDF from resume data.

        FREE operation - does not consume credits.
        """
        try:
            payload = {"resume_data": resume_data}
            if profile_image:
                payload["profile_image"] = profile_image
            if language:
                payload["language"] = language

            async with self._get_client() as client:
                response = await self._request_raw(
                    "POST",
                    "/v1/resumes/generate-pdf/",
                    client,
                    telegram_id=telegram_id,
                    json=payload,
                )
                return response.content
        except Exception as e:
            logger.error(f"Failed to generate PDF for user {telegram_id}: {e}")
            return None

    async def export_resume_pdf(
        self,
        telegram_id: int,
        resume_id: int,
        language: str | None = None,
    ) -> bytes | None:
        """Export a saved resume as PDF.

        FREE operation - does not consume credits.
        """
        try:
            params = {"language": language} if language else {}

            async with self._get_client() as client:
                response = await self._request_raw(
                    "GET",
                    f"/v1/resumes/{resume_id}/export-pdf/",
                    client,
                    telegram_id=telegram_id,
                    params=params,
                )
                return response.content
        except Exception as e:
            logger.error(f"Failed to export PDF for resume {resume_id}: {e}")
            return None
