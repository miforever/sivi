"""Parser for ishkop.uz — job board covering all regions of Uzbekistan.

Strategy: paginate the vacancy list per city. Each card exposes title,
company, salary, location, and a short description snippet — no detail-page
fetches are needed, which keeps request volume low and avoids rate-limiting.
"""

import logging
import random
import re
import time

import httpx
from lxml import html

from apps.vacancies.scraper.base import ParsedVacancy, extract_skills_from_text
from apps.vacancies.scraper.platforms.base import BasePlatformParser

logger = logging.getLogger(__name__)

_BASE_URL = "https://ishkop.uz"
_LIST_PATH = "vacansii"  # transliterated path that supports ?l=city&page=N
_DETAIL_URL = f"{_BASE_URL}/viewjob"
_DEFAULT_REGION = "Ташкент"

# Backoff config for 403/429 responses
_BACKOFF_DELAYS = [5, 15, 30]  # seconds per retry attempt

_SALARY_RE = re.compile(
    r"([\d\s\xa0]+)(?:\s*[-–—]\s*([\d\s\xa0]+))?\s*(UZS|USD|\$|сум|сўм|soʻm)?",
    re.IGNORECASE,
)


def _text(el) -> str:
    return " ".join((el.text_content() or "").split()).strip()


def _to_int(s: str | None) -> int | None:
    if not s:
        return None
    digits = re.sub(r"[^\d]", "", s)
    return int(digits) if digits else None


def _parse_salary(text: str) -> tuple[int | None, int | None, str]:
    if not text:
        return None, None, ""
    match = _SALARY_RE.search(text)
    if not match:
        return None, None, ""
    sal_min = _to_int(match.group(1))
    sal_max = _to_int(match.group(2))
    cur_raw = (match.group(3) or "").lower()
    if cur_raw in ("$", "usd"):
        currency = "USD"
    elif cur_raw:
        currency = "UZS"
    else:
        currency = ""
    return sal_min, sal_max, currency


class IshkopUzParser(BasePlatformParser):
    """Scrapes ishkop.uz vacancy listings for all Uzbekistan regions."""

    platform_name = "ishkop_uz"
    platform_url = "https://ishkop.uz"

    # Maps ishkop URL city slug → canonical region slug.
    # Keys are the path segments used in ishkop.uz/вакансии/<city-slug>.
    # Listed from largest to smallest so high-volume cities are scraped first.
    scrape_regions: dict[str, str] = {
        "Ташкент": "tashkent_city",
        "Андижан": "andijan",
        "Бухара": "bukhara",
        "Самарканд": "samarkand",
        "Фергана": "fergana",
        "Наманган": "namangan",
        "Навои": "navoi",
        "Нукус": "karakalpakstan",
        "Карши": "kashkadarya",
        "Гулистан": "syrdarya",
        "Джизак": "jizzakh",
        "Термез": "surkhandarya",
        "Ургенч": "khorezm",
        "Алмалык-Ташкентская-область": "tashkent_region",
        "Ангрен-Ташкентская-область": "tashkent_region",
        "Бекабад-Ташкентская-область": "tashkent_region",
        "Нурафшон-Ташкентская-область": "tashkent_region",
        "Чирчик-Ташкентская-область": "tashkent_region",
        "Янгиюль-Ташкентская-область": "tashkent_region",
        "Асака-Андижанская-область": "andijan",
        "Коканд-Ферганская-область": "fergana",
        "Маргилан-Ферганская-область": "fergana",
        "Каттакурган-Самаркандская-область": "samarkand",
        "Ургут-Самаркандская-область": "samarkand",
        "Каган-Бухарская-область": "bukhara",
        "Зарафшан-Навоийская-область": "navoi",
        "Шахрисабз-Кашкадарьинская-область": "kashkadarya",
        "Хива-Хорезмская-область": "khorezm",
        "Беруни-Каракалпакстан": "karakalpakstan",
        "Денау-Сурхандарьинская-область": "surkhandarya",
    }

    def __init__(self) -> None:
        self._client = httpx.Client(
            timeout=30.0,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
            },
            follow_redirects=True,
        )

    def _request(self, url: str, params: dict | None = None) -> httpx.Response | None:
        """GET request with exponential backoff on 403/429."""
        for attempt, backoff in enumerate([0, *_BACKOFF_DELAYS]):
            if backoff:
                jitter = random.uniform(0, backoff * 0.3)
                time.sleep(backoff + jitter)
            try:
                resp = self._client.get(url, params=params)
            except httpx.HTTPError:
                logger.exception("ishkop.uz request failed: %s", url)
                continue

            if resp.status_code in (403, 429):
                if attempt < len(_BACKOFF_DELAYS):
                    next_wait = _BACKOFF_DELAYS[attempt]
                    logger.warning(
                        "ishkop.uz %d for %s — backing off %ds (attempt %d/%d)",
                        resp.status_code,
                        url,
                        next_wait,
                        attempt + 1,
                        len(_BACKOFF_DELAYS),
                    )
                    continue
                logger.error(
                    "ishkop.uz %d for %s after %d retries — skipping",
                    resp.status_code,
                    url,
                    len(_BACKOFF_DELAYS),
                )
                return None

            try:
                resp.raise_for_status()
            except httpx.HTTPStatusError:
                logger.warning("ishkop.uz HTTP %d for %s", resp.status_code, url)
                return None

            return resp

        return None

    def fetch_page(self, page: int = 0, **kwargs) -> list[ParsedVacancy]:
        city = kwargs.get("city", _DEFAULT_REGION)
        # Real pagination URL: /vacansii?l=<city>&page=<n>
        # The Cyrillic path /вакансии/<city> ignores ?page=N and always returns page 1.
        list_url = f"{_BASE_URL}/{_LIST_PATH}"
        params: dict = {"l": city}
        if page > 0:
            params["page"] = str(page + 1)

        resp = self._request(list_url, params)
        if resp is None:
            return []

        tree = html.fromstring(resp.text)
        articles = tree.xpath('//article[contains(@class,"job") and @data-id]')
        if not articles:
            return []

        vacancies: list[ParsedVacancy] = []
        for art in articles:
            try:
                vacancy = self._parse_card(art)
                if vacancy:
                    vacancies.append(vacancy)
            except Exception:
                logger.exception("ishkop.uz: failed to parse card")
        return vacancies

    def _parse_card(self, art) -> ParsedVacancy | None:
        data_id = art.get("data-id", "").strip()
        if not data_id:
            return None

        title_els = art.xpath('.//a[contains(@class,"job-title")]')
        if not title_els:
            return None
        title = _text(title_els[0])
        if not title:
            return None

        # Use whole-word class matching so we don't accidentally pick up the
        # wrapping "company-job-data" div when looking for the inner "company".
        def _find(cls: str):
            return art.xpath(
                f'.//*[contains(concat(" ", normalize-space(@class), " "), " job-data ")'
                f' and contains(concat(" ", normalize-space(@class), " "), " {cls} ")]'
            )

        company = ""
        comp_els = _find("company")
        if comp_els:
            company = _text(comp_els[0])

        salary_text = ""
        sal_els = _find("salary")
        if sal_els:
            salary_text = _text(sal_els[0])
        sal_min, sal_max, currency = _parse_salary(salary_text)

        location = ""
        reg_els = _find("region")
        if reg_els:
            # Full address is often in the `title` attribute; fall back to text.
            location = reg_els[0].get("title", "").strip() or _text(reg_els[0])
        if not location:
            location = _DEFAULT_REGION

        source_url = f"{_DETAIL_URL}?id={data_id}"

        # Extract description from the card itself — no detail-page fetch needed.
        # Ishkop cards expose a short snippet in a "desc" or "text" element.
        description = self._extract_card_description(art) or title
        skills = extract_skills_from_text(f"{title} {description}")

        return ParsedVacancy(
            title=title,
            description=description,
            company=company,
            salary_min=sal_min,
            salary_max=sal_max,
            salary_currency=currency,
            location=location,
            skills=skills,
            language="ru",
            source_url=source_url,
        )

    def _extract_card_description(self, art) -> str:
        """Pull whatever description text is visible on the listing card."""
        # Try known element patterns for short description snippets on cards
        for xpath in [
            './/*[contains(@class,"job-desc")]',
            './/*[contains(@class,"job-description")]',
            './/*[contains(@class,"desc")]',
            './/*[contains(@class,"snippet")]',
            ".//p",
        ]:
            els = art.xpath(xpath)
            if els:
                text = _text(els[0])
                if text:
                    return text
        return ""

    def close(self) -> None:
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
