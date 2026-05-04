"""Parser for @ishmi_ish (Ishmi-ish | IT va Boshqa Vakansiyalar) channel.

Format: Uzbek (Latin), highly structured emoji-section template.
Structure (post body only — channel title is not included in raw_text):
    <emoji> <Job title> kerak
    💰 Maosh: ...
    💼 Tajriba: ...
    🛠 Dasturlar|Texnologiya: ...         (optional)
    📚 Fan/Yo'nalish: ...                  (optional)
    📋 Talablar:
    • ...
    📍 Manzil: ...
    🌐 Format: Offline|Online|Hybrid
    👉 Batafsil: Link
    📌 Obuna bo'ling: @ishmi_ish
    #hashtags
"""

import re
from datetime import datetime

from apps.vacancies.scraper.channels.base import BaseChannelParser, ParsedVacancy


class IshmiIshParser(BaseChannelParser):
    channel_username = "ishmi_ish"
    channel_name = "Ishmi-ish | IT va Boshqa Vakansiyalar"

    _FOOTER_MARKERS = ["📌 Obuna bo'ling", "📌 Obuna bo`ling", "👉 Batafsil"]
    _TITLE_SUFFIX_RE = re.compile(r"\s+kerak\s*$", re.IGNORECASE)
    _SECTION_PREFIXES = ("💰", "💼", "📋", "📍", "🌐", "👉", "📌", "📚", "🛠", "•", "#")

    def is_vacancy(self, message: dict) -> bool:
        text = message.get("raw_text", "")
        if not text:
            return False
        # Structural fingerprint: Maosh + Talablar + Manzil are always present
        markers = ("Maosh", "Talablar", "Manzil")
        hits = sum(1 for m in markers if m in text)
        return hits >= 2 and ("kerak" in text.lower() or "@ishmi_ish" in text)

    def extract(self, message: dict) -> ParsedVacancy | None:
        text = message.get("raw_text", "")
        text_clean = self.clean_footer(text, self._FOOTER_MARKERS)

        lines = [ln.strip() for ln in text_clean.split("\n")]

        # Title: first line ending with "kerak" (strip that suffix)
        title = ""
        for line in lines:
            if not line:
                continue
            if self._TITLE_SUFFIX_RE.search(line):
                title = self._TITLE_SUFFIX_RE.sub("", line).strip()
                break
        # Fallback: first non-empty, non-section line
        if not title:
            for line in lines:
                if not line or line.startswith(self._SECTION_PREFIXES):
                    continue
                title = line
                break

        if not title:
            return None

        salary_text = self.get_field_value(text_clean, ["Maosh", "💰 Maosh"])
        sal_min, sal_max, sal_currency = self.extract_salary(salary_text)

        location = self.get_field_value(text_clean, ["Manzil", "📍 Manzil"])

        experience_text = self.get_field_value(text_clean, ["Tajriba", "💼 Tajriba"])
        experience_years = self.extract_experience(experience_text) or self.extract_experience(
            text_clean
        )

        format_text = self.get_field_value(text_clean, ["Format", "🌐 Format"])
        work_format = self.detect_work_format(format_text) or self.detect_work_format(text_clean)

        return ParsedVacancy(
            title=title,
            description=text_clean,
            company="",
            salary_min=sal_min,
            salary_max=sal_max,
            salary_currency=sal_currency,
            location=location,
            work_format=work_format,
            employment_type=self.detect_employment_type(text_clean),
            experience_years=experience_years,
            skills=self.extract_skills(text_clean),
            contact_info=self.extract_contacts(text_clean),
            language="uz",
            posted_at=self._parse_date(message),
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
