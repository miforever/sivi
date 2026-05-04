"""Parser for hh.uz via the hh.ru REST API (area=97, Uzbekistan).

List endpoint   → snippet-based description, no key_skills (fast, default)
Detail endpoint → full HTML description + key_skills (slow, opt-in)

API base: https://api.hh.ru/
Auth: not required for vacancy search/read.
"""

import logging
import re
import time
from datetime import datetime
from html.parser import HTMLParser

import httpx
from httpx import HTTPStatusError

from apps.vacancies.scraper.base import ParsedVacancy
from apps.vacancies.scraper.platforms.base import BasePlatformParser

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_BASE_URL = "https://api.hh.ru"
_AREA_UZ = 97  # Uzbekistan country code — used when no specific area is set
_PER_PAGE = 100  # API maximum
_API_PAGE_LIMIT = 20  # hh.ru caps results at 2000 (20 x 100) per area query

_EXPERIENCE_MAP: dict[str, int] = {
    "noExperience": 0,
    "between1And3": 1,
    "between3And6": 3,
    "moreThan6": 6,
}

_EMPLOYMENT_MAP: dict[str, str] = {
    "full": "full_time",
    "part": "part_time",
    "project": "contract",
    "volunteer": "freelance",
    "probation": "internship",
}

# work_format[].id → our work_format value
_WORK_FORMAT_MAP: dict[str, str] = {
    "ON_SITE": "office",
    "REMOTE": "remote",
    "HYBRID": "hybrid",
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


class HhUzParser(BasePlatformParser):
    """Fetches vacancies from hh.uz across all Uzbekistan regions.

    Uses per-region area queries to work around the hh.ru API cap of 2 000
    results per query. Each entry in ``scrape_regions`` maps an HH area ID
    (the major city of that region) to a canonical region slug. Region is
    resolved from the vacancy's location field by the normalizer rather than
    from the area ID, so jobs listed under a city's area but physically
    located elsewhere are still tagged correctly.

    Args:
        fetch_details: If True, makes an extra GET per vacancy to retrieve
                       the full HTML description and key_skills. Significantly
                       slower but richer data.
        text: Optional keyword filter forwarded to the API (e.g. "python").
    """

    platform_name = "hh_uz"
    platform_url = "https://hh.uz"

    # Maps every HH area ID in Uzbekistan → empty region slug.
    # Region slug is intentionally empty: the normalizer resolves the correct
    # region from the vacancy's location field (city name provided by hh.uz).
    # Querying each city separately bypasses the 2 000-result cap that applies
    # to the country-wide area=97 query. Most small cities return <1 page;
    # only Tashkent is likely to approach the per-area cap.
    # fmt: off
    scrape_regions: dict[str, str] = {
        "2759": "", "2763": "", "2764": "", "2765": "", "2766": "",
        "2767": "", "2768": "", "2769": "", "2770": "", "2771": "",
        "2772": "", "2773": "", "2774": "", "2775": "", "2776": "",
        "2777": "", "2778": "", "2779": "", "2780": "", "2781": "",
        "2782": "", "2783": "", "2784": "", "2785": "", "2786": "",
        "2787": "", "2788": "", "2789": "", "2790": "", "2791": "",
        "2859": "", "2860": "", "2861": "", "2862": "", "2863": "",
        "2864": "", "2865": "", "2866": "", "2867": "", "2868": "",
        "2869": "", "2870": "", "2871": "", "2872": "", "2873": "",
        "2874": "", "2875": "", "2876": "", "2877": "", "2878": "",
        "2879": "", "2880": "", "2881": "", "2882": "", "2883": "",
        "2884": "", "2885": "", "2886": "", "2887": "", "2888": "",
        "2889": "", "2890": "", "2891": "", "2892": "", "2893": "",
        "2894": "", "2895": "", "2896": "", "2897": "", "2898": "",
        "2899": "", "2900": "", "2901": "", "2902": "", "2903": "",
        "2904": "", "2905": "", "2906": "", "2907": "", "2908": "",
        "2909": "", "2910": "", "2911": "", "2912": "", "2913": "",
        "2914": "", "2915": "", "2916": "", "2917": "", "2918": "",
        "2919": "", "2920": "", "2921": "", "2922": "", "2923": "",
        "2924": "", "2925": "", "2926": "", "2927": "", "2928": "",
        "2929": "", "2930": "", "2931": "", "2932": "", "2933": "",
        "2934": "", "2935": "", "2936": "", "2937": "", "2938": "",
        "2939": "", "2940": "", "2941": "", "2942": "", "2943": "",
        "6381": "", "17529": "", "17530": "", "17531": "", "17532": "",
    }
    # fmt: on

    def __init__(self, fetch_details: bool = False, text: str = "") -> None:
        self._fetch_details = fetch_details
        self._text = text
        self._client = httpx.Client(
            headers={
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
        if page >= _API_PAGE_LIMIT:
            return []

        # city kwarg holds the HH area ID (string) when scrape_regions is used.
        area_raw = kwargs.get("city", _AREA_UZ)
        try:
            area = int(area_raw)
        except (TypeError, ValueError):
            area = _AREA_UZ

        params: dict = {
            "area": area,
            "per_page": _PER_PAGE,
            "page": page,
            "order_by": "publication_time",
        }
        text = kwargs.get("text", self._text)
        if text:
            params["text"] = text

        resp = self._request_with_retry(f"{_BASE_URL}/vacancies", params=params)
        if resp is None:
            return []

        data = resp.json()
        items = data.get("items") or []

        if not items or page >= data.get("pages", 0):
            return []

        vacancies = []
        for item in items:
            try:
                if self._fetch_details:
                    item = self._get_detail(item["id"]) or item
                vacancies.append(self._map(item))
            except Exception:
                logger.exception("hh.uz mapping failed for item %s", item.get("id"))
        return vacancies

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _request_with_retry(self, url: str, params: dict | None = None) -> httpx.Response | None:
        """GET with retry + backoff on 403/429."""
        delay = 2
        for attempt in range(4):
            try:
                resp = self._client.get(url, params=params)
                resp.raise_for_status()
                return resp
            except HTTPStatusError as exc:
                if exc.response.status_code in (403, 429) and attempt < 3:
                    logger.warning(
                        "hh.uz %d for %s, retrying in %ds", exc.response.status_code, url, delay
                    )
                    time.sleep(delay)
                    delay *= 2
                    continue
                logger.exception("hh.uz request failed: %s", url)
                return None
            except httpx.HTTPError:
                logger.exception("hh.uz request failed: %s", url)
                return None
        return None

    def _get_detail(self, vacancy_id: str) -> dict | None:
        """Fetch full vacancy detail (description HTML + key_skills)."""
        resp = self._request_with_retry(f"{_BASE_URL}/vacancies/{vacancy_id}")
        if resp is None:
            return None
        return resp.json()

    def _map(self, item: dict) -> ParsedVacancy:
        # --- salary ---
        salary = item.get("salary") or {}
        sal_min: int | None = salary.get("from")
        sal_max: int | None = salary.get("to")
        sal_currency: str = salary.get("currency", "")

        # --- description ---
        # Detail view: full HTML description
        # List view: snippet (plain text, may be None)
        if item.get("description"):
            description = _strip_html(item["description"])
        else:
            snippet = item.get("snippet") or {}
            parts = filter(
                None,
                [
                    snippet.get("responsibility"),
                    snippet.get("requirement"),
                ],
            )
            description = "\n\n".join(parts)

        # --- skills ---
        key_skills: list[str] = [s["name"] for s in (item.get("key_skills") or []) if s.get("name")]

        # --- location ---
        area = item.get("area") or {}
        location = area.get("name", "")

        # --- experience ---
        exp_id = (item.get("experience") or {}).get("id", "")
        experience_years: int | None = _EXPERIENCE_MAP.get(exp_id)

        # --- employment type ---
        emp_id = (item.get("employment") or {}).get("id", "")
        employment_type = _EMPLOYMENT_MAP.get(emp_id, "full_time")

        # --- work format ---
        # Prefer structured work_format list, fallback to schedule.id
        work_format = ""
        wf_list = item.get("work_format") or []
        if wf_list:
            work_format = _WORK_FORMAT_MAP.get(wf_list[0].get("id", ""), "")
        if not work_format:
            sched_id = (item.get("schedule") or {}).get("id", "")
            if sched_id == "remote":
                work_format = "remote"

        # --- posted_at ---
        posted_at: datetime | None = None
        if pub := item.get("published_at"):
            try:
                posted_at = datetime.fromisoformat(pub)
            except (ValueError, TypeError):
                pass

        return ParsedVacancy(
            title=item.get("name", ""),
            description=description,
            company=(item.get("employer") or {}).get("name", ""),
            salary_min=sal_min,
            salary_max=sal_max,
            salary_currency=sal_currency,
            employment_type=employment_type,
            work_format=work_format,
            location=location,
            experience_years=experience_years,
            skills=key_skills,
            contact_info="",
            language="ru",
            posted_at=posted_at,
            source_url=item.get("alternate_url", ""),
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
