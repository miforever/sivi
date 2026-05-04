"""Parser for osonish.uz job board.

API (reverse-engineered from frontend):
    GET https://osonish.uz/api/v1/vacancies?page={page}
    GET https://osonish.uz/api/v1/vacancies/{id}   ← detail (has info HTML)

Pagination: 1-based page index, 30 results per page.
No authentication required for public listings.
"""

import logging
import re
from datetime import datetime
from html.parser import HTMLParser

import httpx

from apps.vacancies.scraper.base import ParsedVacancy, extract_skills_from_text
from apps.vacancies.scraper.platforms.base import BasePlatformParser

logger = logging.getLogger(__name__)

_BASE_URL = "https://osonish.uz/api/v1"
_SOURCE_URL = "https://osonish.uz/vacancies/{id}"

# busyness_type → employment_type
_BUSYNESS_MAP: dict[int, str] = {
    1: "full_time",
    2: "part_time",
    3: "contract",
    4: "freelance",
    5: "internship",
}

# work_type → work_format
_WORK_TYPE_MAP: dict[int, str] = {
    1: "office",
    2: "remote",
    3: "hybrid",
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


class OsonishUzParser(BasePlatformParser):
    """Fetches vacancies from osonish.uz."""

    platform_name = "osonish_uz"
    platform_url = "https://osonish.uz"

    def __init__(self) -> None:
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
        # osonish.uz uses 1-based pagination
        api_page = page + 1
        params: dict = {"page": api_page}
        if search := kwargs.get("search", ""):
            params["search"] = search

        try:
            resp = self._client.get(f"{_BASE_URL}/vacancies", params=params)
            resp.raise_for_status()
        except httpx.HTTPError:
            logger.exception("osonish.uz request failed (page=%d)", api_page)
            return []

        data = resp.json()
        if not data.get("success"):
            return []

        page_data = data.get("data", {})
        items = page_data.get("data") or []
        last_page = page_data.get("last_page", 1)

        if not items or api_page > last_page:
            return []

        vacancies = []
        for item in items:
            try:
                vacancies.append(self._map(item))
            except Exception:
                logger.exception("osonish.uz mapping failed for item %s", item.get("id"))
        return vacancies

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _map(self, item: dict) -> ParsedVacancy:
        vacancy_id = item.get("id", "")

        # --- title ---
        title = item.get("title", "")
        # Use canonical position name if title is vague or missing
        mmk_position = item.get("mmk_position") or {}
        if not title and mmk_position:
            title = mmk_position.get("position_name", "")

        # --- description ---
        description = _strip_html(item.get("info") or "")
        if not description:
            # Build fallback from structured metadata so the vacancy passes is_valid
            mmk_group = item.get("mmk_group") or {}
            parts = filter(
                None,
                [
                    mmk_group.get("cat2") or mmk_group.get("cat1"),
                    item.get("title", ""),
                ],
            )
            description = " | ".join(parts)

        # --- company ---
        company_obj = item.get("company") or {}
        company = company_obj.get("name", "")

        # --- salary ---
        sal_min_raw = item.get("min_salary")
        sal_max_raw = item.get("max_salary")
        sal_min: int | None = int(sal_min_raw) if sal_min_raw else None
        sal_max: int | None = int(sal_max_raw) if sal_max_raw else None
        sal_currency = "UZS" if (sal_min or sal_max) else ""

        # --- location ---
        location_parts = []
        filial = item.get("filial") or {}
        if address := (item.get("address") or filial.get("address") or ""):
            location_parts.append(address)
        location = ", ".join(location_parts)

        # --- experience ---
        exp_raw = item.get("work_experiance")
        experience_years: int | None = int(exp_raw) if exp_raw else None

        # --- employment type ---
        busyness = item.get("busyness_type")
        employment_type = _BUSYNESS_MAP.get(busyness, "full_time") if busyness else "full_time"

        # --- work format ---
        work_type = item.get("work_type")
        work_format = _WORK_TYPE_MAP.get(work_type, "") if work_type else ""

        # --- skills ---
        skills_details = item.get("skills_details") or item.get("skills") or []
        if skills_details:
            skills = [s.get("name", "") for s in skills_details if s.get("name")]
        else:
            skills = extract_skills_from_text(description)

        # --- contact ---
        hr_obj = item.get("hr") or {}
        contact_info = hr_obj.get("phone", "") or item.get("additional_phone", "")

        # --- posted_at ---
        posted_at: datetime | None = None
        for date_field in ("created_at", "updated_at"):
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
            work_format=work_format,
            location=location,
            experience_years=experience_years,
            skills=skills,
            contact_info=contact_info,
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
