"""Parser for corp.uzairways.com — official Uzbekistan Airways careers page.

Strategy: single list page `/en/vacancy` enumerates all open positions as
`<a class="inner-content-link shadow-box" href="/en/node/NNNN">`. Each
detail page has the title in `h1.page-heading` and the job body inside
`<main>`. The vacancy set is small (usually fewer than ~30 active roles),
so everything is collected on the first call.
"""

import logging

import httpx
from lxml import html

from apps.vacancies.scraper.base import ParsedVacancy
from apps.vacancies.scraper.platforms.base import BasePlatformParser

logger = logging.getLogger(__name__)

_BASE_URL = "https://corp.uzairways.com"
_LIST_URL = f"{_BASE_URL}/en/vacancy"


def _text(el) -> str:
    return " ".join((el.text_content() or "").split()).strip()


class UzairwaysParser(BasePlatformParser):
    """Scrapes official Uzbekistan Airways vacancies."""

    platform_name = "uzairways"
    platform_url = _BASE_URL

    def __init__(self) -> None:
        self._client = httpx.Client(
            timeout=30.0,
            headers={"User-Agent": "Mozilla/5.0 (compatible; SiviBot/1.0)"},
            follow_redirects=True,
        )

    def fetch_page(self, page: int = 0, **kwargs) -> list[ParsedVacancy]:
        # Single-page list — return everything on page 0, empty after.
        if page > 0:
            return []

        try:
            resp = self._client.get(_LIST_URL)
            resp.raise_for_status()
        except httpx.HTTPError:
            logger.exception("uzairways list request failed")
            return []

        tree = html.fromstring(resp.text)
        links = tree.xpath(
            '//a[contains(@class,"inner-content-link")'
            ' and contains(@class,"shadow-box") and contains(@href,"/en/node/")]'
        )
        if not links:
            return []

        vacancies: list[ParsedVacancy] = []
        seen: set[str] = set()
        for link in links:
            href = (link.get("href") or "").strip()
            if not href or href in seen:
                continue
            seen.add(href)

            title = _text(link)
            # Skip the stray "CV" link (application form entry point).
            if not title or title.upper() == "CV" or len(title) < 8:
                continue

            detail_url = href if href.startswith("http") else f"{_BASE_URL}{href}"
            try:
                vacancy = self._fetch_detail(title, detail_url)
                if vacancy:
                    vacancies.append(vacancy)
            except Exception:
                logger.exception("uzairways: detail fetch failed for %s", detail_url)
        return vacancies

    def _fetch_detail(self, title: str, url: str) -> ParsedVacancy | None:
        try:
            resp = self._client.get(url)
            resp.raise_for_status()
        except httpx.HTTPError:
            logger.warning("uzairways: failed to fetch %s", url)
            return None

        tree = html.fromstring(resp.text)

        # Detail title overrides the list-link title when available.
        h1_els = tree.xpath('//h1[contains(@class,"page-heading")]')
        if h1_els:
            detail_title = _text(h1_els[0])
            if detail_title:
                title = detail_title

        # Body — prefer <main>, otherwise fall back to page-content div.
        body_els = tree.xpath("//main") or tree.xpath('//div[contains(@class,"page-content")]')
        description = _text(body_els[0]) if body_els else ""
        if not description:
            description = title

        return ParsedVacancy(
            title=title,
            description=description,
            company="Uzbekistan Airways",
            location="Tashkent",
            region="tashkent_city",
            language="en",
            source_url=url,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
