"""Parser for vacandi.uz — Uzbekistan job platform.

JSON API with cursor-based pagination.
API base: https://api.vacandi.uz/
Auth: not required for public vacancy search.
"""

import logging
import re
from datetime import datetime

import httpx

from apps.vacancies.scraper.base import ParsedVacancy, extract_skills_from_text
from apps.vacancies.scraper.platforms.base import BasePlatformParser

logger = logging.getLogger(__name__)

_BASE_URL = "https://api.vacandi.uz"
_PER_PAGE = 100

_EMPLOYMENT_MAP: dict[str, str] = {
    "FULL": "full_time",
    "PART": "part_time",
    "CONTRACT": "contract",
    "INTERNSHIP": "internship",
    "FREELANCE": "freelance",
}

_REMOTE_MAP: dict[str, str] = {
    "ON_SITE": "office",
    "REMOTE": "remote",
    "HYBRID": "hybrid",
}

_EXPERIENCE_MAP: dict[str, int] = {
    "no_experience": 0,
    "up_to_1": 0,
    "1_to_3": 1,
    "3_to_6": 3,
    "5_plus": 5,
    "more_than_6": 6,
}

_MAX_SALARY = 2_000_000_000  # PostgreSQL int4 safe limit


class VacandiUzParser(BasePlatformParser):
    """Fetches vacancies from vacandi.uz JSON API (cursor pagination)."""

    platform_name = "vacandi_uz"
    platform_url = "https://vacandi.uz"

    def __init__(self) -> None:
        self._client = httpx.Client(
            headers={
                "User-Agent": "sivi-job-aggregator/1.0 (aggregator; uz)",
                "Accept": "application/json",
            },
            timeout=30.0,
        )
        self._next_cursor: str | None = None

    # ------------------------------------------------------------------
    # Override fetch_all for cursor-based pagination
    # ------------------------------------------------------------------

    def fetch_all(self, max_pages: int = 1000, **kwargs) -> list[ParsedVacancy]:
        """Fetch all pages using cursor pagination."""
        results: list[ParsedVacancy] = []
        cursor: str | None = None

        for _ in range(max_pages):
            batch, cursor = self._fetch_with_cursor(cursor, **kwargs)
            if not batch:
                break
            results.extend(batch)
            if cursor is None:
                break
        return results

    def fetch_page(self, page: int = 0, **kwargs) -> list[ParsedVacancy]:
        """Fetch a single page. For cursor APIs, page > 0 uses stored cursor."""
        if page == 0:
            self._next_cursor = None
        batch, self._next_cursor = self._fetch_with_cursor(self._next_cursor, **kwargs)
        return batch

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _fetch_with_cursor(
        self, cursor: str | None = None, **kwargs
    ) -> tuple[list[ParsedVacancy], str | None]:
        """Fetch one page; returns (vacancies, next_cursor_or_None)."""
        params: dict = {"limit": _PER_PAGE}
        if cursor:
            params["cursor"] = cursor

        try:
            resp = self._client.get(f"{_BASE_URL}/vacancies", params=params)
            resp.raise_for_status()
        except httpx.HTTPError:
            logger.exception("vacandi.uz request failed")
            return [], None

        data = resp.json()
        items = data.get("items") or []
        if not items:
            return [], None

        pagination = data.get("pagination") or {}
        next_cursor = pagination.get("nextCursor") if pagination.get("hasMore") else None

        vacancies: list[ParsedVacancy] = []
        for item in items:
            try:
                vacancies.append(self._map(item))
            except Exception:
                logger.exception("vacandi.uz mapping failed for %s", item.get("id"))
        return vacancies, next_cursor

    @staticmethod
    def _safe_salary(raw) -> int | None:
        if raw is None:
            return None
        try:
            val = int(float(raw))
        except (ValueError, TypeError, OverflowError):
            return None
        if val <= 0 or val > _MAX_SALARY:
            return None
        return val

    def _map(self, item: dict) -> ParsedVacancy:
        # --- salary ---
        sal_min: int | None = self._safe_salary(item.get("salary_min"))
        sal_max: int | None = self._safe_salary(item.get("salary_max"))
        sal_currency: str = item.get("currency", "UZS")

        # --- employment type ---
        emp_raw = item.get("employment_type", "")
        employment_type = _EMPLOYMENT_MAP.get(emp_raw, "full_time")

        # --- work format ---
        remote_raw = item.get("remote_type") or ""
        work_format = _REMOTE_MAP.get(remote_raw, "")

        # --- experience ---
        exp_raw = item.get("experience") or ""
        experience_years = _EXPERIENCE_MAP.get(exp_raw)

        # --- company ---
        company_obj = item.get("companies") or {}
        company = company_obj.get("name", "")

        # --- location ---
        location = item.get("location") or ""
        if not location:
            # Extract from description: "Адрес: ..." or "Manzil: ..."
            desc = item.get("description", "")
            loc_match = re.search(r"(?:Адрес|Manzil|Манзил)\s*:\s*(.+?)(?:\n|$)", desc)
            if loc_match:
                location = loc_match.group(1).strip()

        # --- posted_at ---
        posted_at: datetime | None = None
        if ts := item.get("created_at"):
            try:
                posted_at = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                pass

        vacancy_id = item.get("id", "")
        title = item.get("title", "")
        description = item.get("description", "")
        skills = extract_skills_from_text(f"{title} {description}")

        return ParsedVacancy(
            title=title,
            description=description,
            company=company,
            salary_min=sal_min,
            salary_max=sal_max,
            salary_currency=sal_currency,
            employment_type=employment_type,
            work_format=work_format,
            location=location,
            experience_years=experience_years,
            skills=skills,
            contact_info="",
            language="uz",
            posted_at=posted_at,
            source_url=f"https://vacandi.uz/vacancies/{vacancy_id}" if vacancy_id else "",
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
