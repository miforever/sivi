"""Base class for platform (API/website) vacancy parsers."""

from abc import ABC, abstractmethod

from apps.vacancies.scraper.base import ParsedVacancy as ParsedVacancy


class BasePlatformParser(ABC):
    """Base class for job platform parsers (REST APIs, structured websites).

    Unlike channel parsers which process raw Telegram messages, platform
    parsers fetch data directly from structured APIs and map it to
    ParsedVacancy objects.

    Subclasses must set `platform_name` and `platform_url`,
    and implement `fetch_page()`.
    """

    platform_name: str  # e.g. "hh_uz"
    platform_url: str  # e.g. "https://hh.uz"

    @abstractmethod
    def fetch_page(self, page: int = 0, **kwargs) -> list[ParsedVacancy]:
        """Fetch one page of vacancies from the platform.

        Args:
            page: Zero-based page index.
            **kwargs: Platform-specific filters (keywords, area, etc.).

        Returns:
            List of ParsedVacancy objects for this page.
            Return an empty list when there are no more results.
        """
        ...

    def fetch_all(self, max_pages: int = 1000, **kwargs) -> list[ParsedVacancy]:
        """Fetch all pages up to `max_pages`. Stops early on empty page."""
        results: list[ParsedVacancy] = []
        for page in range(max_pages):
            batch = self.fetch_page(page=page, **kwargs)
            if not batch:
                break
            results.extend(batch)
        return results
