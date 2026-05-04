"""Resume management API."""

import logging
from typing import Any

from src.services.backend.base import _BackendClient

logger = logging.getLogger(__name__)


class ResumeAPI(_BackendClient):
    """API for resume CRUD and AI operations."""

    async def get_user_resumes(self, telegram_id: int) -> list[dict[str, Any]]:
        """Get all resumes for a user."""
        result = await self._handle_request(
            "GET",
            "/v1/resumes/",
            telegram_id=telegram_id,
            error_msg=f"Failed to get resumes for user {telegram_id}",
        )
        return result if isinstance(result, list) else []

    async def get_resume_detail(self, telegram_id: int, resume_id: int) -> dict[str, Any]:
        """Get detailed information about a resume."""
        return await self._handle_request(
            "GET",
            f"/v1/resumes/{resume_id}/",
            telegram_id=telegram_id,
            error_msg=f"Failed to get resume detail for resume {resume_id}",
        )

    async def save_resume(self, telegram_id: int, resume_data: dict) -> dict[str, Any]:
        """Save resume to backend."""
        if not isinstance(resume_data, dict):
            raise ValueError("resume_data must be a dict.")

        # Normalize key: AI returns "education" but backend expects "educations"
        if "education" in resume_data and "educations" not in resume_data:
            resume_data["educations"] = resume_data.pop("education")

        # Ensure title is present (required by backend)
        if not resume_data.get("title"):
            position = resume_data.get("position", "").strip()
            full_name = resume_data.get("full_name", "").strip()
            resume_data["title"] = position or full_name or "My Resume"

        # Sanitize nested objects: drop entries missing backend-required fields
        if "experiences" in resume_data:
            resume_data["experiences"] = [
                exp
                for exp in resume_data["experiences"]
                if exp.get("company", "").strip() and exp.get("position", "").strip()
            ]
        if "educations" in resume_data:
            resume_data["educations"] = [
                edu
                for edu in resume_data["educations"]
                if edu.get("institution", "").strip() and edu.get("degree", "").strip()
            ]
        if "certifications" in resume_data:
            resume_data["certifications"] = [
                cert for cert in resume_data["certifications"] if cert.get("name", "").strip()
            ]

        return await self._handle_request(
            "POST",
            "/v1/resumes/",
            telegram_id=telegram_id,
            json=resume_data,
            error_msg=f"Failed to save resume for user {telegram_id}",
        )

    async def delete_resume(self, telegram_id: int, resume_id: str) -> bool:
        """Delete a resume."""
        try:
            async with self._get_client() as client:
                response = await self._request_raw(
                    "DELETE",
                    f"/v1/resumes/{resume_id}/",
                    client,
                    telegram_id=telegram_id,
                )
                return response.status_code == 204
        except Exception:
            return False

    async def extract_resume(
        self,
        telegram_id: int,
        file_bytes: bytes,
        file_type: str = "pdf",
        language: str | None = None,
    ):
        """Extract structured resume data from a file.

        Subject to weekly AI call limit.
        """
        import httpx as _httpx

        from src.services.backend.base import WeeklyLimitReachedError

        try:
            files = {
                "file": (
                    f"resume.{file_type}",
                    file_bytes,
                    f"application/{file_type}",
                )
            }
            params = {"language": language} if language else {}

            async with self._get_client() as client:
                response = await client.post(
                    f"{self.base_url}/v1/resumes/extract/",
                    files=files,
                    params=params,
                    headers=self._get_headers(telegram_id),
                )
                response.raise_for_status()
                result = response.json()
                data = result.get("data", {})

                resume_data = data.get("resume_data", {})
                credits_remaining = data.get("credits_remaining", 0)

                return resume_data, credits_remaining

        except _httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                try:
                    body = e.response.json()
                    msg = body.get("error", {}).get("message", "Weekly limit reached")
                except Exception:
                    msg = "Weekly limit reached"
                raise WeeklyLimitReachedError(msg) from e
            logger.error(f"Failed to extract resume for user {telegram_id}: {e}")
            return {}
        except WeeklyLimitReachedError:
            raise
        except Exception as e:
            logger.error(f"Failed to extract resume for user {telegram_id}: {e}")
            return {}

    async def generate_resume_from_qa(
        self,
        telegram_id: int,
        qa_pairs: list[dict[str, Any]],
        user_info: dict[str, Any],
        language: str | None = None,
        position: str | None = None,
    ) -> dict[str, Any]:
        """Generate structured resume data from Q&A.

        Consumes 1 credit per generation.
        """
        payload = {"qa_pairs": qa_pairs, "user_info": user_info}
        if language:
            payload["language"] = language
        if position:
            payload["position"] = position

        result = await self._handle_request(
            "POST",
            "/v1/resumes/generate-from-qa/",
            telegram_id=telegram_id,
            json=payload,
            error_msg=f"Failed to generate resume from QA for user {telegram_id}",
        )

        resume_data = result.get("resume_data", {})
        credits_remaining = result.get("credits_remaining", 0)

        return resume_data, credits_remaining

    async def enhance_resume(
        self,
        telegram_id: int,
        resume_id: int,
        language: str | None = None,
    ) -> dict[str, Any]:
        """Enhance an existing resume using AI.

        Consumes 1 credit per enhancement.
        """
        payload = {}
        if language:
            payload["language"] = language

        result = await self._handle_request(
            "POST",
            f"/v1/resumes/{resume_id}/enhance/",
            telegram_id=telegram_id,
            json=payload,
            error_msg=f"Failed to enhance resume {resume_id}",
        )

        # Return resume_data and credits_remaining
        return {
            "resume_data": result.get("resume_data", {}),
            "credits_remaining": result.get("credits_remaining", 0),
        }
