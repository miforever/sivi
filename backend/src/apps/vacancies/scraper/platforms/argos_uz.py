"""Parser for vacancy.argos.uz — Uzbekistan's unified civil-service vacancy portal.

API endpoint (internal, reverse-engineered from frontend):
    POST https://hrm.argos.uz/api/Vacancy/HRMVacancy/GetHRMVacancyList

Pagination: 0-based ``page`` index, 10 results per page.
No authentication required for public listings.
"""

import logging
from datetime import datetime

import httpx

from apps.vacancies.scraper.base import ParsedVacancy, extract_skills_from_text
from apps.vacancies.scraper.platforms.base import BasePlatformParser

logger = logging.getLogger(__name__)

_API_URL = "https://hrm.argos.uz/api/Vacancy/HRMVacancy/GetHRMVacancyList"
_DETAIL_URL = "https://vacancy.argos.uz/hrm-vacancy-detail/{id}"
_PAGE_SIZE = 10


class ArgosUzParser(BasePlatformParser):
    """Fetches civil-service vacancies from vacancy.argos.uz."""

    platform_name = "argos_uz"
    platform_url = "https://vacancy.argos.uz"

    def __init__(self) -> None:
        self._client = httpx.Client(
            headers={
                "Content-Type": "application/json",
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
            },
            timeout=30.0,
        )

    # ------------------------------------------------------------------
    # BasePlatformParser interface
    # ------------------------------------------------------------------

    def fetch_page(self, page: int = 0, **kwargs) -> list[ParsedVacancy]:
        payload = {
            "page": page,
            "search": kwargs.get("search", ""),
            "regionSoato": kwargs.get("regionSoato"),
            "districtSoato": kwargs.get("districtSoato"),
            "organizationId": kwargs.get("organizationId"),
            "fatherOrganizationId": kwargs.get("fatherOrganizationId"),
            "civilServant": kwargs.get("civilServant"),
            "vacancyType": kwargs.get("vacancyType"),
            "isDisablity": kwargs.get("isDisablity"),
            "isInternal": kwargs.get("isInternal"),
            "minSalary": kwargs.get("minSalary"),
            "workExperience": kwargs.get("workExperience"),
            "organizationTin": kwargs.get("organizationTin"),
        }

        try:
            resp = self._client.post(_API_URL, json=payload)
            resp.raise_for_status()
        except httpx.HTTPError:
            logger.exception("argos.uz request failed (page=%d)", page)
            return []

        data = resp.json()
        items = data.get("results") or []

        if not items:
            return []

        vacancies = []
        for item in items:
            try:
                vacancies.append(self._map(item))
            except Exception:
                logger.exception("argos.uz mapping failed for item %s", item.get("id"))
        return vacancies

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _map(self, item: dict) -> ParsedVacancy:
        vacancy_id = item.get("id", "")

        # --- title ---
        title = item.get("position_name", "")

        # --- description: combine duties, requirements, conditions ---
        parts = filter(
            None,
            [
                item.get("position_duties"),
                item.get("position_requirements"),
                item.get("position_conditions"),
            ],
        )
        description = "\n\n".join(parts)
        if not description:
            # Fall back to structure name so the vacancy is not discarded as invalid
            description = item.get("structure_name", "")

        # --- company ---
        company = item.get("organization", "")

        # --- salary ---
        raw_salary = item.get("position_salary") or 0
        sal_min: int | None = int(raw_salary) if raw_salary else None
        sal_max: int | None = None
        sal_currency = "UZS" if sal_min else ""

        # --- location ---
        location = item.get("region", "")

        # --- experience ---
        exp_raw = item.get("experience")
        experience_years: int | None = int(exp_raw) if exp_raw else None

        # --- skills (extracted from free-text fields) ---
        skills_text = " ".join(
            filter(
                None,
                [
                    description,
                    item.get("position_mark_surcharge", ""),
                ],
            )
        )
        skills = extract_skills_from_text(skills_text)

        # --- posted_at ---
        posted_at: datetime | None = None
        for date_field in ("created", "date_start"):
            raw_date = item.get(date_field)
            if raw_date:
                try:
                    posted_at = datetime.fromisoformat(raw_date)
                    break
                except (ValueError, TypeError):
                    pass

        # --- source URL ---
        source_url = _DETAIL_URL.format(id=vacancy_id) if vacancy_id else ""

        return ParsedVacancy(
            title=title,
            description=description,
            company=company,
            salary_min=sal_min,
            salary_max=sal_max,
            salary_currency=sal_currency,
            employment_type="full_time",  # civil service positions are always full-time
            work_format="office",  # civil service positions are always on-site
            location=location,
            experience_years=experience_years,
            skills=skills,
            contact_info="",
            language="uz",
            posted_at=posted_at,
            source_url=source_url,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
