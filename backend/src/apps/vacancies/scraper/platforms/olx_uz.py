"""Parser for OLX.uz — Uzbekistan classifieds job section.

Uses the OLX internal JSON API (``/api/v1/offers``).
Job listings sit under several sub-category IDs; we query by keyword
and filter for job-related categories to avoid non-job noise.

API base: https://www.olx.uz/api/v1/
Auth: not required.
"""

import logging
import re
from datetime import datetime

import httpx

from apps.vacancies.scraper.base import ParsedVacancy, extract_skills_from_text
from apps.vacancies.scraper.platforms.base import BasePlatformParser

logger = logging.getLogger(__name__)

_BASE_URL = "https://www.olx.uz/api/v1"
_PER_PAGE = 50
_JOB_CATEGORY_ID = 6  # OLX top-level "Работа" category (all job listings)

_JOB_TYPE_MAP: dict[str, str] = {
    "Постоянная работа": "full_time",
    "Полная занятость": "full_time",
    "Частичная занятость": "part_time",
    "Временная работа": "contract",
    "Стажировка": "internship",
    "Фриланс": "freelance",
}


class OlxUzParser(BasePlatformParser):
    """Fetches job vacancies from OLX.uz JSON API."""

    platform_name = "olx_uz"
    platform_url = "https://www.olx.uz"

    def __init__(self) -> None:
        self._client = httpx.Client(
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json",
            },
            timeout=30.0,
        )

    def fetch_page(self, page: int = 0, **kwargs) -> list[ParsedVacancy]:
        offset = page * _PER_PAGE
        params: dict = {
            "offset": offset,
            "limit": _PER_PAGE,
            "category_id": _JOB_CATEGORY_ID,
            "sort_by": "created_at:desc",
        }

        try:
            resp = self._client.get(f"{_BASE_URL}/offers", params=params)
            resp.raise_for_status()
        except httpx.HTTPError:
            logger.exception("OLX.uz request failed (offset=%d)", offset)
            return []

        data = resp.json()
        items = data.get("data") or []
        if not items:
            return []

        vacancies: list[ParsedVacancy] = []
        for item in items:
            try:
                vacancies.append(self._map(item))
            except Exception:
                logger.exception("OLX.uz mapping failed for item %s", item.get("id"))
        return vacancies

    def _map(self, item: dict) -> ParsedVacancy:
        # --- params extraction ---
        params = {p["key"]: p for p in (item.get("params") or []) if "key" in p}

        # --- salary ---
        sal_min: int | None = None
        sal_max: int | None = None
        sal_currency = ""
        pg_int_max = 2_147_483_647
        salary_param = params.get("salary", {})
        if salary_param:
            sal_value = salary_param.get("value") or {}
            sal_min = sal_value.get("from")
            sal_max = sal_value.get("to")
            sal_currency = sal_value.get("currency", "UZS")
            if sal_min and sal_min > pg_int_max:
                sal_min = pg_int_max
            if sal_max and sal_max > pg_int_max:
                sal_max = pg_int_max

        # --- employment type ---
        employment_type = "full_time"
        job_type_param = params.get("job_type", {})
        if job_type_param:
            jt_label = (job_type_param.get("value") or {}).get("label", "")
            employment_type = _JOB_TYPE_MAP.get(jt_label, "full_time")

        # --- work format ---
        work_format = "office"
        remote_param = params.get("remote_work", {})
        if remote_param:
            rv = remote_param.get("value") or {}
            if rv.get("key") == "yes" or rv.get("label") in ("Да", "Yes"):
                work_format = "remote"

        # --- location ---
        loc = item.get("location") or {}
        city = (loc.get("city") or {}).get("name", "")
        region = (loc.get("region") or {}).get("name", "")
        location = city or region

        # --- posted_at ---
        posted_at: datetime | None = None
        if ts := item.get("created_time"):
            try:
                posted_at = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                pass

        # --- description ---
        description = item.get("description") or item.get("title", "")
        # Strip HTML tags from OLX descriptions
        description = re.sub(r"<[^>]+>", " ", description)
        description = re.sub(r"\s+", " ", description).strip()

        title = item.get("title", "")
        skills = extract_skills_from_text(f"{title} {description}")

        return ParsedVacancy(
            title=title,
            description=description,
            company=(item.get("user") or {}).get("name", ""),
            salary_min=sal_min,
            salary_max=sal_max,
            salary_currency=sal_currency,
            employment_type=employment_type,
            work_format=work_format,
            location=location,
            experience_years=None,
            skills=skills,
            contact_info="",
            language="uz",
            posted_at=posted_at,
            source_url=item.get("url", ""),
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
