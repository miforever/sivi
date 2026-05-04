"""Resume service for managing resume data with caching."""

import logging
from typing import Any

from src.services.backend import BackendService, BackendServiceError
from src.services.cache import Cache, CacheError

logger = logging.getLogger(__name__)


class ResumeService:
    """Service for fetching and caching resume data."""

    def __init__(self, cache: Cache, backend: BackendService):
        """
        Initialize the resume service.

        Args:
            cache: Cache service instance
            backend: Backend service instance
        """
        self.cache = cache
        self.backend = backend

    # ==================== Resume Retrieval ====================

    async def get_user_resumes(self, telegram_id: int, force_refresh: bool = False) -> list[dict[str, Any]]:
        """Get all resumes for a user from cache or backend."""
        if not force_refresh:
            try:
                cached_resumes = await self.cache.get_user_resumes(telegram_id)
                if cached_resumes:
                    logger.debug("User %s resumes found in cache", telegram_id)
                    return cached_resumes
            except CacheError as e:
                logger.warning("Cache retrieval failed for user %s resumes: %s", telegram_id, str(e))

        return await self._fetch_and_cache_resumes(telegram_id)

    async def get_resume_detail(
        self, telegram_id: int, resume_id: int, force_refresh: bool = False
    ) -> dict[str, Any] | None:
        """Get detailed information about a specific resume."""
        if not force_refresh:
            try:
                cached_resume = await self.cache.get_user_resume(telegram_id, resume_id)
                if cached_resume:
                    logger.debug("Resume %s found in cache for user %s", resume_id, telegram_id)
                    return cached_resume
            except CacheError as e:
                logger.warning("Cache retrieval failed for resume %s: %s", resume_id, str(e))

        try:
            resume = await self.backend.get_resume_detail(telegram_id, resume_id)

            if resume:
                await self._update_resume_in_cache(telegram_id, resume)
                return resume

            logger.debug("Resume %s not found for user %s", resume_id, telegram_id)
            return None

        except BackendServiceError as e:
            logger.error("Backend error fetching resume %s: %s", resume_id, str(e))
            return None

    async def _fetch_and_cache_resumes(self, telegram_id: int) -> list[dict[str, Any]]:
        """Fetch resumes from backend and cache the result."""
        try:
            resumes = await self.backend.get_user_resumes(telegram_id)

            if resumes:
                try:
                    await self.cache.save_user_resumes(telegram_id, resumes)
                    logger.debug("Cached %d resumes for user %s", len(resumes), telegram_id)
                except CacheError as e:
                    logger.warning("Failed to cache resumes for user %s: %s", telegram_id, str(e))

            return resumes

        except BackendServiceError as e:
            logger.error("Backend error fetching resumes for user %s: %s", telegram_id, str(e))
            return []

    async def _update_resume_in_cache(self, telegram_id: int, resume: dict[str, Any]) -> None:
        """Update a single resume in the cached resume list."""
        try:
            resumes = await self.cache.get_user_resumes(telegram_id)
            resume_id = resume.get("id")

            updated = False
            for i, r in enumerate(resumes):
                if r.get("id") == resume_id:
                    resumes[i] = resume
                    updated = True
                    break

            if not updated:
                resumes.append(resume)

            await self.cache.save_user_resumes(telegram_id, resumes)
            logger.debug("Updated resume %s in cache for user %s", resume_id, telegram_id)

        except CacheError as e:
            logger.warning("Failed to update resume in cache: %s", str(e))

    # ==================== Resume Creation ====================

    async def save_resume(self, telegram_id: int, resume_data: dict) -> dict[str, Any] | None:
        """Save a new resume to backend and update cache."""
        try:
            saved_resume = await self.backend.save_resume(telegram_id, resume_data)

            if saved_resume and not saved_resume.get("error"):
                await self._update_resume_in_cache(telegram_id, saved_resume)
                logger.debug("Saved and cached new resume for user %s", telegram_id)
                return saved_resume

            logger.error("Failed to save resume for user %s: %s", telegram_id, saved_resume)
            return None

        except BackendServiceError as e:
            logger.error("Backend error saving resume for user %s: %s", telegram_id, str(e))
            return None

    async def extract_resume(
        self, telegram_id: int, file_bytes: bytes, file_type: str = "pdf", language: str | None = None
    ) -> dict[str, Any] | None:
        """
        Extract structured resume data from a file.
        FREE operation - does not consume credits.

        Returns:
            Dict with resume_data and credits_remaining, or None on error
        """
        try:
            result = await self.backend.extract_resume(telegram_id, file_bytes, file_type, language)

            if result and result.get("resume_data"):
                logger.debug("Successfully extracted resume for user %s", telegram_id)

                # Invalidate credits cache since we got updated balance
                try:
                    await self.cache.delete_user_credits(telegram_id)
                except CacheError:
                    pass

                return result

            logger.warning("Resume extraction returned empty data for user %s", telegram_id)
            return None

        except Exception as e:
            logger.error("Error extracting resume for user %s: %s", telegram_id, str(e))
            return None

    async def generate_from_qa(
        self,
        telegram_id: int,
        qa_pairs: list[dict[str, Any]],
        user_info: dict[str, Any],
        language: str | None = None,
        position: str | None = None,
    ) -> dict[str, Any] | None:
        """
        Generate structured resume data from Q&A pairs.
        Consumes 1 credit per generation.

        Returns:
            Dict with resume_data and credits_remaining, or None on error
        """
        try:
            result = await self.backend.generate_resume_from_qa(telegram_id, qa_pairs, user_info, language, position)

            if result and result.get("resume_data"):
                logger.debug("Generated resume from QA for user %s", telegram_id)

                # Invalidate credits cache since balance changed
                try:
                    await self.cache.delete_user_credits(telegram_id)
                except CacheError:
                    pass

                return result

            logger.warning("Resume generation from QA returned empty data for user %s", telegram_id)
            return None

        except BackendServiceError as e:
            logger.error("Backend error generating resume from QA for user %s: %s", telegram_id, str(e))
            return None

    # ==================== Resume Enhancement ====================

    async def enhance_resume(
        self, telegram_id: int, resume_id: int, language: str | None = None
    ) -> dict[str, Any] | None:
        """
        Enhance an existing resume using AI.
        Consumes 1 credit per enhancement.

        Returns:
            Dict with resume_data and credits_remaining, or None on error
        """
        try:
            result = await self.backend.enhance_resume(telegram_id, resume_id, language)

            if result and result.get("resume_data"):
                # Update cache with enhanced version
                enhanced_resume = result.get("resume_data")
                await self._update_resume_in_cache(telegram_id, enhanced_resume)

                # Invalidate credits cache
                try:
                    await self.cache.delete_user_credits(telegram_id)
                except CacheError:
                    pass

                logger.debug("Enhanced and cached resume %s for user %s", resume_id, telegram_id)
                return result

            logger.error("Failed to enhance resume %s for user %s", resume_id, telegram_id)
            return None

        except BackendServiceError as e:
            logger.error("Backend error enhancing resume %s: %s", resume_id, str(e))
            return None

    # ==================== Resume Deletion ====================

    async def delete_resume(self, telegram_id: int, resume_id: str) -> bool:
        """Delete a resume from backend and cache."""
        try:
            success = await self.backend.delete_resume(telegram_id, resume_id)

            if success:
                try:
                    resumes = await self.cache.get_user_resumes(telegram_id)
                    resumes = [r for r in resumes if r.get("id") != int(resume_id)]
                    await self.cache.save_user_resumes(telegram_id, resumes)
                    logger.debug("Deleted resume %s from cache for user %s", resume_id, telegram_id)
                except CacheError as e:
                    logger.warning("Failed to remove resume from cache: %s", str(e))

                return True

            logger.error("Failed to delete resume %s for user %s", resume_id, telegram_id)
            return False

        except Exception as e:
            logger.error("Error deleting resume %s: %s", resume_id, str(e))
            return False

    # ==================== PDF Generation ====================

    async def generate_pdf(
        self,
        telegram_id: int,
        resume_data: dict[str, Any],
        profile_image: str | None = None,
        language: str | None = None,
    ) -> bytes | None:
        """
        Generate a PDF from resume data.
        FREE operation - does not consume credits.
        """
        try:
            pdf_bytes = await self.backend.generate_pdf_from_resume(telegram_id, resume_data, profile_image, language)

            if pdf_bytes:
                logger.debug("Generated PDF for user %s", telegram_id)
                return pdf_bytes

            logger.error("Failed to generate PDF for user %s", telegram_id)
            return None

        except Exception as e:
            logger.error("Error generating PDF for user %s: %s", telegram_id, str(e))
            return None

    async def export_pdf(self, telegram_id: int, resume_id: int, language: str | None = None) -> bytes | None:
        """
        Export a saved resume as PDF.
        FREE operation - does not consume credits.
        """
        try:
            pdf_bytes = await self.backend.export_resume_pdf(telegram_id, resume_id, language)

            if pdf_bytes:
                logger.debug("Exported PDF for resume %s, user %s", resume_id, telegram_id)
                return pdf_bytes

            logger.error("Failed to export PDF for resume %s", resume_id)
            return None

        except Exception as e:
            logger.error("Error exporting PDF for resume %s: %s", resume_id, str(e))
            return None

    # ==================== Credit Management ====================

    async def get_credit_packages(self, telegram_id: int, force_refresh: bool = False) -> list[dict[str, Any]]:
        """
        Get available credit packages.

        Args:
            force_refresh: If True, bypass cache and fetch from backend

        Returns:
            List of credit packages with pricing
        """
        if not force_refresh:
            try:
                cached_packages = await self.cache.get_credit_packages()
                if cached_packages:
                    logger.debug("Retrieved credit packages from cache")
                    return cached_packages
            except CacheError as e:
                logger.warning("Cache retrieval failed for credit packages: %s", str(e))

        # Fetch from backend
        try:
            packages = await self.backend.get_credit_packages(telegram_id)

            if packages:
                # Cache the result
                try:
                    await self.cache.set_credit_packages(packages)
                    logger.debug("Cached credit packages")
                except CacheError as e:
                    logger.warning("Failed to cache credit packages: %s", str(e))

                return packages

            return []

        except BackendServiceError as e:
            logger.error("Backend error fetching credit packages: %s", str(e))
            return []

    async def purchase_credits(
        self,
        telegram_id: int,
        credits: int,
        payment_id: str,
        payment_provider: str = "click",
        amount_paid: float | None = None,
        currency: str = "UZS",
    ) -> dict[str, Any]:
        """
        Process credit purchase after successful payment.
        Invalidates credits cache on success.
        """
        result = await self.backend.purchase_credits(
            telegram_id, credits, payment_id, payment_provider, amount_paid, currency
        )

        if result.get("success"):
            # Invalidate credits cache to force fresh fetch
            try:
                await self.cache.delete_user_credits(telegram_id)
                logger.debug("Invalidated credits cache for user %s after purchase", telegram_id)
            except CacheError as e:
                logger.warning("Failed to invalidate credits cache: %s", str(e))

        return result

    async def get_user_credits(self, telegram_id: int, force_refresh: bool = False) -> dict[str, Any]:
        """
        Get user's credit balance and statistics.

        Returns:
            Dict with current_balance and statistics
        """
        if not force_refresh:
            try:
                cached_credits = await self.cache.get_user_credits(telegram_id)
                if cached_credits:
                    logger.debug("Retrieved credits from cache for user %s", telegram_id)
                    return cached_credits
            except CacheError as e:
                logger.warning("Cache retrieval failed for credits: %s", str(e))

        # Fetch from backend
        try:
            credits_data = await self.backend.get_user_credits(telegram_id)

            if credits_data:
                # Cache the result
                try:
                    await self.cache.set_user_credits(telegram_id, credits_data)
                    logger.debug("Cached credits for user %s", telegram_id)
                except CacheError as e:
                    logger.warning("Failed to cache credits: %s", str(e))

                return credits_data

            return {"current_balance": 0, "statistics": {}}

        except BackendServiceError as e:
            logger.error("Backend error fetching credits: %s", str(e))
            return {"current_balance": 0, "statistics": {}}

    async def get_credit_history(
        self, telegram_id: int, transaction_type: str | None = None, limit: int = 50
    ) -> dict[str, Any]:
        """
        Get user's credit transaction history.

        Returns:
            Dict with transactions list, count, and current_balance
        """
        try:
            history = await self.backend.get_credit_history(telegram_id, transaction_type, limit)

            if history:
                logger.debug("Retrieved credit history for user %s", telegram_id)
                return history

            return {"transactions": [], "count": 0, "current_balance": 0}

        except BackendServiceError as e:
            logger.error("Backend error fetching credit history: %s", str(e))
            return {"transactions": [], "count": 0, "current_balance": 0}

    # ==================== Questions ====================

    async def get_questions(self, language: str, position: str) -> list[dict[str, Any]]:
        """Get questions for resume creation."""
        try:
            questions = await self.backend.get_questions(language, position)
            logger.debug("Retrieved %d questions for %s/%s", len(questions), language, position)
            return questions

        except BackendServiceError as e:
            logger.error("Backend error fetching questions: %s", str(e))
            return []

    # ==================== Resume Answers (Temporary Data) ====================

    async def save_resume_answers(self, telegram_id: int, answers: dict[str, Any], ttl: int | None = None) -> bool:
        """Save resume answers to cache (temporary form data)."""
        try:
            await self.cache.set_resume_answers(telegram_id, answers, ttl)
            logger.debug("Saved resume answers for user %s", telegram_id)
            return True
        except CacheError as e:
            logger.error("Failed to save resume answers for user %s: %s", telegram_id, str(e))
            return False

    async def get_resume_answers(self, telegram_id: int) -> dict[str, Any]:
        """Get resume answers from cache."""
        try:
            answers = await self.cache.get_resume_answers(telegram_id)
            logger.debug("Retrieved resume answers for user %s", telegram_id)
            return answers
        except CacheError as e:
            logger.error("Failed to get resume answers for user %s: %s", telegram_id, str(e))
            return {}

    async def clear_resume_answers(self, telegram_id: int) -> bool:
        """Clear resume answers from cache."""
        try:
            await self.cache.clear_resume_answers(telegram_id)
            logger.debug("Cleared resume answers for user %s", telegram_id)
            return True
        except CacheError as e:
            logger.error("Failed to clear resume answers for user %s: %s", telegram_id, str(e))
            return False

    # ==================== Cache Management ====================

    async def invalidate_cache(self, telegram_id: int) -> None:
        """Invalidate resume cache for a user."""
        try:
            await self.cache.save_user_resumes(telegram_id, [])
            logger.debug("Invalidated resume cache for user %s", telegram_id)
        except CacheError as e:
            logger.warning("Failed to invalidate resume cache for user %s: %s", telegram_id, str(e))

    async def refresh_resumes(self, telegram_id: int) -> list[dict[str, Any]]:
        """Force refresh resumes from backend, bypassing cache."""
        await self.invalidate_cache(telegram_id)
        return await self._fetch_and_cache_resumes(telegram_id)
