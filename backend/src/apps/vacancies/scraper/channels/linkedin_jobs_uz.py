"""Parser for @linkedinjobsuzbekistan channel.

Re-posts LinkedIn job listings for Uzbekistan in a highly consistent format:

    🆕 {Company} is hiring a {Title} in {Location}.
    🔗 https://uz.linkedin.com/jobs/view/{slug}-{id}
    👉 Search by Hashtag: #{Hashtag}
    🙌 Sharing is caring @linkedinjobsuzbekistan

Variants seen:
  - "{Company} is hiring a {Title} in {Location}."
  - "{Company} is hiring an {Title} in {Location}."
  - "{Company} hiring {Title} in {Location}"   (no "is", no "a/an", no period)
  - "{Company} is hiring a {Title} for {Location} (m/f/d)."
"""

import re
from datetime import datetime

from apps.vacancies.scraper.channels.base import BaseChannelParser, ParsedVacancy

# Main header line: "Company is hiring a Title in Location"
_HEADER_RE = re.compile(
    r"""
    (?:🆕\s*)?                     # optional marker
    (?P<company>.+?)\s+             # company (lazy)
    (?:is\s+)?hiring\s+             # "is hiring" or "hiring"
    (?:an?\s+)?                     # optional "a"/"an"
    (?P<title>.+)\s+                # title (greedy — consume through title's own "in"s)
    (?:in|for)\s+                   # LAST "in" or "for" before location
    (?P<location>[^.\n]+?)          # location (no period or newline)
    \.?\s*$                         # optional trailing period
    """,
    re.VERBOSE | re.MULTILINE | re.IGNORECASE,
)

_LINKEDIN_URL_RE = re.compile(
    r"https?://(?:[a-z]{2,3}\.)?linkedin\.com/jobs/view/\S+",
    re.IGNORECASE,
)

_HASHTAG_RE = re.compile(r"#(\w+)")

# m/f/d and similar gender-neutral markers found in German-origin postings
_TITLE_NOISE_RE = re.compile(r"\s*\(m/f/d\)|\s*\(m/w/d\)", re.IGNORECASE)


class LinkedInJobsUzParser(BaseChannelParser):
    channel_username = "linkedinjobsuzbekistan"
    channel_name = "LinkedIn Jobs Uzbekistan"

    _FOOTER_MARKERS = [
        "🙌 Sharing is caring",
        "Follow us on Facebook",
        "Sharing is caring",
    ]

    def is_vacancy(self, message: dict) -> bool:
        text = message.get("raw_text", "") or message.get("text", "")
        if not text or len(text) < 30:
            return False
        if "hiring" not in text.lower():
            return False
        return bool(_LINKEDIN_URL_RE.search(text)) or bool(_HEADER_RE.search(text))

    def extract(self, message: dict) -> ParsedVacancy | None:
        text = (message.get("raw_text") or message.get("text") or "").strip()
        text_clean = self.clean_footer(text, self._FOOTER_MARKERS)

        match = _HEADER_RE.search(text_clean)
        if not match:
            return None

        company = match.group("company").strip()
        title = _TITLE_NOISE_RE.sub("", match.group("title")).strip()
        location = match.group("location").strip().rstrip(",.")

        if not title or not company:
            return None

        # LinkedIn job URL (preferred source URL)
        source_url = ""
        url_match = _LINKEDIN_URL_RE.search(text_clean)
        if url_match:
            source_url = url_match.group(0).rstrip(".,)")

        # Hashtags become informal skills/keywords
        hashtags = _HASHTAG_RE.findall(text_clean)
        # Skip the channel handle
        hashtags = [h for h in hashtags if h.lower() != "linkedinjobsuzbekistan"]

        return ParsedVacancy(
            title=title,
            description=text_clean,
            company=company,
            location=location,
            work_format=self.detect_work_format(text_clean),
            employment_type=self.detect_employment_type(text_clean),
            skills=self.extract_skills(text_clean) or hashtags,
            contact_info="",
            language="en",
            posted_at=self._parse_date(message),
            source_url=source_url,
        )

    @staticmethod
    def _parse_date(message: dict):
        date_str = message.get("date")
        if date_str:
            try:
                return datetime.fromisoformat(date_str)
            except (ValueError, TypeError):
                pass
        return None
