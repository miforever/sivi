"""Parser for ishplus.uz — Uzbekistan job board (HTML scraper).

The site is server-rendered Laravel/Livewire with no public JSON API.
We scrape paginated HTML list pages and optionally fetch each detail page
for full requirements/duties/conditions text.

List URL:   https://ishplus.uz/vacancies?page={N}   (1-based, 30/page)
Detail URL: https://ishplus.uz/vacancy/{id}/{slug}
"""

import logging
import re
from datetime import datetime
from html.parser import HTMLParser

import httpx

from apps.vacancies.scraper.base import ParsedVacancy, extract_skills_from_text
from apps.vacancies.scraper.platforms.base import BasePlatformParser

logger = logging.getLogger(__name__)

_LIST_URL = "https://ishplus.uz/vacancies"
_DETAIL_URL = "https://ishplus.uz{path}"
_SOURCE_URL = "https://ishplus.uz{path}"


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


def _clean(text: str) -> str:
    """Decode HTML entities and collapse whitespace."""
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&quot;", '"', text)
    text = re.sub(r"&#039;", "'", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    text = re.sub(r"&[a-z]+;", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _extract_salary(text: str) -> tuple[int | None, int | None, str]:
    """Parse Uzbek salary text into (min, max, currency)."""
    if not text or any(w in text.lower() for w in ["suxbat", "kelishiladi", "muzokarali"]):
        return None, None, ""
    # Remove non-breaking spaces and separators
    text = text.replace("\xa0", " ").replace(" ", "")
    # Find numbers (salary amounts in so'm)
    numbers = [
        int(n.replace(" ", ""))
        for n in re.findall(r"\d[\d\s]{2,}", text)
        if int(re.sub(r"\s", "", n)) > 100_000
    ]
    if not numbers:
        return None, None, ""
    sal_min = min(numbers)
    sal_max = max(numbers) if len(numbers) > 1 else None
    return sal_min, sal_max, "UZS"


def _parse_date(text: str) -> datetime | None:
    """Parse 'Chop etildi: DD.MM.YYYY' → datetime."""
    m = re.search(r"(\d{2})\.(\d{2})\.(\d{4})", text)
    if m:
        try:
            return datetime(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        except ValueError:
            pass
    return None


def _last_page(html: str) -> int:
    """Extract last page number from pagination HTML."""
    pages = re.findall(r"[?&]page=(\d+)", html)
    return max((int(p) for p in pages), default=1)


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


class IshplusUzParser(BasePlatformParser):
    """Fetches vacancies from ishplus.uz by scraping paginated HTML."""

    platform_name = "ishplus_uz"
    platform_url = "https://ishplus.uz"

    def __init__(self, fetch_details: bool = False) -> None:
        self._fetch_details = fetch_details
        self._last_page: int | None = None
        self._client = httpx.Client(
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                "Accept-Language": "uz,ru;q=0.9",
            },
            timeout=30.0,
            follow_redirects=True,
        )

    # ------------------------------------------------------------------
    # BasePlatformParser interface
    # ------------------------------------------------------------------

    def fetch_page(self, page: int = 0, **kwargs) -> list[ParsedVacancy]:
        # ishplus.uz uses 1-based pagination
        api_page = page + 1

        # Stop early once we know the last page
        if self._last_page is not None and api_page > self._last_page:
            return []

        params: dict = {"page": api_page}
        if search := kwargs.get("search", ""):
            params["search"] = search
        if city := kwargs.get("city"):
            params["city"] = city

        try:
            resp = self._client.get(_LIST_URL, params=params)
            resp.raise_for_status()
        except httpx.HTTPError:
            logger.exception("ishplus.uz list request failed (page=%d)", api_page)
            return []

        html = resp.text

        # Cache last page on first fetch
        if self._last_page is None:
            self._last_page = _last_page(html)

        items = self._parse_list(html)
        if not items:
            return []

        if self._fetch_details:
            enriched = []
            for item in items:
                try:
                    detail = self._fetch_detail(item["path"])
                    if detail:
                        item.update(detail)
                except Exception:
                    logger.exception("ishplus.uz detail fetch failed for %s", item.get("path"))
                enriched.append(item)
            items = enriched

        vacancies = []
        for item in items:
            try:
                vacancies.append(self._map(item))
            except Exception:
                logger.exception("ishplus.uz mapping failed for %s", item.get("path"))
        return vacancies

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _parse_list(self, html: str) -> list[dict]:
        """Extract vacancy dicts from list page HTML."""
        # Each vacancy is wrapped in <div class="item"> containing <h6 class="name">
        item_pattern = re.compile(
            r'<div class="img"[^>]*>.*?'  # img block
            r'<div class="text">(.*?)'  # text block start
            r"</div>\s*</div>\s*</div>",  # end of item
            re.DOTALL,
        )

        results = []
        for m in item_pattern.finditer(html):
            block = m.group(1)

            # Title & URL
            link_m = re.search(r'href="(/vacancy/[^"]+)"[^>]*>([^<]+)</a>', block)
            if not link_m:
                continue
            path = link_m.group(1)
            title = _clean(link_m.group(2))

            # Organization
            org_m = re.search(
                r'class="org[^"]*">.*?Tashkilot:\s*</span>\s*([^<]+)', block, re.DOTALL
            )
            company = _clean(org_m.group(1)) if org_m else ""

            # Location
            addr_m = re.search(r'class="address">([^<]+)', block)
            location = _clean(addr_m.group(1)) if addr_m else ""

            # Salary text
            price_m = re.search(r'class="price">([^<]+)', block)
            salary_text = _clean(price_m.group(1)) if price_m else ""

            # Date
            date_m = re.search(r'class="date">([^<]+)', block)
            date_text = _clean(date_m.group(1)) if date_m else ""

            results.append(
                {
                    "path": path,
                    "title": title,
                    "company": company,
                    "location": location,
                    "salary_text": salary_text,
                    "date_text": date_text,
                    "description": "",
                }
            )
        return results

    def _fetch_detail(self, path: str) -> dict | None:
        """Fetch detail page and return enriched fields."""
        try:
            resp = self._client.get(_DETAIL_URL.format(path=path))
            resp.raise_for_status()
        except httpx.HTTPError:
            logger.warning("ishplus.uz detail request failed: %s", path)
            return None

        html = resp.text

        parts = []

        # Requirements
        req_m = re.search(
            r'Talablar:.*?<div class="list">(.*?)</div>\s*</div>',
            html,
            re.DOTALL,
        )
        if req_m:
            parts.append("Talablar:\n" + _strip_html(req_m.group(1)))

        # Duties
        duties_m = re.search(
            r'Ish vazifalari:.*?<div class="list">(.*?)</div>\s*</div>',
            html,
            re.DOTALL,
        )
        if duties_m:
            parts.append("Ish vazifalari:\n" + _strip_html(duties_m.group(1)))

        # Conditions
        cond_m = re.search(
            r'Ish sharoitlari:.*?<div class="list">(.*?)</div>\s*</div>',
            html,
            re.DOTALL,
        )
        if cond_m:
            parts.append("Ish sharoitlari:\n" + _strip_html(cond_m.group(1)))

        # Phone/contact
        phone_m = re.search(r"(\+998[\d\s\-]{8,})", html)
        contact = phone_m.group(1).strip() if phone_m else ""

        # Salary (may be richer on detail page)
        price_m = re.search(r'class="price">([^<]+)', html)
        salary_text = _clean(price_m.group(1)) if price_m else ""

        return {
            "description": "\n\n".join(parts),
            "contact_info": contact,
            "salary_text": salary_text,
        }

    def _map(self, item: dict) -> ParsedVacancy:
        sal_min, sal_max, sal_currency = _extract_salary(item.get("salary_text", ""))

        description = item.get("description", "")
        if not description:
            # Build a minimal description from available metadata
            parts = filter(
                None,
                [
                    item.get("company"),
                    item.get("location"),
                    item.get("salary_text"),
                ],
            )
            description = " | ".join(parts)

        return ParsedVacancy(
            title=item.get("title", ""),
            description=description,
            company=item.get("company", ""),
            salary_min=sal_min,
            salary_max=sal_max,
            salary_currency=sal_currency,
            employment_type="",
            work_format="",
            location=item.get("location", ""),
            experience_years=None,
            skills=extract_skills_from_text(description),
            contact_info=item.get("contact_info", ""),
            language="uz",
            posted_at=_parse_date(item.get("date_text", "")),
            source_url=_SOURCE_URL.format(path=item.get("path", "")),
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
