"""Parser for ish.uz job board.

API (reverse-engineered from frontend, base: VUE_APP_API_BASE_URL):
    GET https://ish.uz/api/api/v1/vacancies?page={page}   ← list
    GET https://ish.uz/api/api/v1/vacancies/{id}          ← detail (vacancy_detail HTML)

Pagination: 1-based page index, 20 results per page.
No authentication required for public listings.

Note: ``fetch_details=True`` makes one extra GET per vacancy to retrieve the full
HTML description. Significantly slower but richer data.
"""

import logging
import re
from datetime import datetime
from html.parser import HTMLParser

import httpx

from apps.vacancies.scraper.base import ParsedVacancy, extract_skills_from_text
from apps.vacancies.scraper.platforms.base import BasePlatformParser

logger = logging.getLogger(__name__)

_BASE_URL = "https://ish.uz/api/api/v1"
_SOURCE_URL = "https://ish.uz/jobs/{id}"

# work_experience_id → years
_EXPERIENCE_MAP: dict[int, int] = {
    1: 0,  # no experience
    2: 1,
    3: 3,
    4: 5,
}

# employment_type_id → our value
_EMPLOYMENT_MAP: dict[int, str] = {
    1: "full_time",
    2: "part_time",
    3: "contract",
    4: "freelance",
    5: "internship",
}


# ---------------------------------------------------------------------------
# HTML → plain text
# ---------------------------------------------------------------------------


class _HTMLStripper(HTMLParser):
    _BLOCK_TAGS = {"li", "br", "p", "div", "h1", "h2", "h3", "h4", "tr"}

    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in self._BLOCK_TAGS:
            self._parts.append("\n")

    def handle_data(self, data: str) -> None:
        self._parts.append(data)

    def get_text(self) -> str:
        raw = "".join(self._parts)
        raw = re.sub(r"[ \t]+", " ", raw)
        raw = re.sub(r"\n{3,}", "\n\n", raw)
        return raw.strip()


def _strip_html(html: str) -> str:
    if not html:
        return ""
    stripper = _HTMLStripper()
    stripper.feed(html)
    return stripper.get_text()


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


class IshUzParser(BasePlatformParser):
    """Fetches vacancies from ish.uz."""

    platform_name = "ish_uz"
    platform_url = "https://ish.uz"

    def __init__(self, fetch_details: bool = True) -> None:
        self._fetch_details = fetch_details
        self._client = httpx.Client(
            headers={
                "Accept": "application/json",
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
        # ish.uz uses 1-based pagination
        api_page = page + 1
        params: dict = {"page": api_page}
        if search := kwargs.get("search", ""):
            params["search"] = search

        try:
            resp = self._client.get(f"{_BASE_URL}/vacancies", params=params)
            resp.raise_for_status()
        except httpx.HTTPError:
            logger.exception("ish.uz request failed (page=%d)", api_page)
            return []

        outer = resp.json()
        if not outer.get("success"):
            return []

        page_data = outer.get("data", {})
        items = page_data.get("data") or []
        last_page = page_data.get("last_page", 1)

        if not items or api_page > last_page:
            return []

        vacancies = []
        for item in items:
            try:
                if self._fetch_details:
                    detail = self._get_detail(item["id"])
                    if detail:
                        item = {**item, **detail}
                vacancies.append(self._map(item))
            except Exception:
                logger.exception("ish.uz mapping failed for item %s", item.get("id"))
        return vacancies

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_detail(self, vacancy_id: int) -> dict | None:
        try:
            resp = self._client.get(f"{_BASE_URL}/vacancies/{vacancy_id}")
            resp.raise_for_status()
            outer = resp.json()
            if outer.get("success"):
                return outer.get("data") or {}
        except httpx.HTTPError:
            logger.warning("ish.uz detail fetch failed for id=%s", vacancy_id)
        return None

    def _map(self, item: dict) -> ParsedVacancy:
        vacancy_id = item.get("id", "")

        # --- title ---
        title = item.get("position_name", "")

        # --- description ---
        description = _strip_html(item.get("vacancy_detail") or "")

        # --- company ---
        company_obj = item.get("company") or {}
        company = company_obj.get("name", "") or item.get("company_name", "")

        # --- salary ---
        salary_hidden = item.get("salary_hidden", False)
        if not salary_hidden:
            sal_from = item.get("salary_from")
            sal_to = item.get("salary_to")
            sal_min: int | None = int(float(sal_from)) if sal_from else None
            sal_max: int | None = int(float(sal_to)) if sal_to else None
            sal_currency = item.get("salary_currency", "UZS")
        else:
            sal_min = sal_max = None
            sal_currency = ""

        # --- location ---
        regions = item.get("regions") or []
        location = regions[0].get("name_oz", "") if regions else ""
        if address := item.get("address", ""):
            location = f"{location}, {address}".strip(", ")

        # --- experience ---
        exp_id = item.get("work_experience_id")
        experience_years: int | None = _EXPERIENCE_MAP.get(exp_id) if exp_id else None

        # --- employment type ---
        emp_ids = item.get("employment_type_id") or []
        employment_type = _EMPLOYMENT_MAP.get(emp_ids[0], "full_time") if emp_ids else "full_time"

        # --- skills ---
        skills = extract_skills_from_text(description)

        # --- posted_at ---
        posted_at: datetime | None = None
        for date_field in ("published_at", "created_at"):
            raw_date = item.get(date_field)
            if raw_date:
                try:
                    posted_at = datetime.fromisoformat(raw_date)
                    break
                except (ValueError, TypeError):
                    pass

        return ParsedVacancy(
            title=title,
            description=description,
            company=company,
            salary_min=sal_min,
            salary_max=sal_max,
            salary_currency=sal_currency,
            employment_type=employment_type,
            work_format="",
            location=location,
            experience_years=experience_years,
            skills=skills,
            contact_info="",
            language="uz",
            posted_at=posted_at,
            source_url=_SOURCE_URL.format(id=vacancy_id) if vacancy_id else "",
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
