"""Parser for @data_ish (DATA | ISH) channel.

Format: Uzbek (Latin + Cyrillic), emoji-section markers.
Structure:
    Job Title + "ishga taklif qilinadi"
    📌 Talablar: (bullet points with •)
    ✅ Qulayliklar/Vazifalar: (bullet points)
    • Ish vaqti: ...
    • Maosh: ...
    📍 Manzil: ...
    ☎️ Aloqa: phone / @handle
    Footer: @Data_bandlik @data_ish
"""

import re

from apps.vacancies.scraper.channels.base import BaseChannelParser, ParsedVacancy


class DataIshParser(BaseChannelParser):
    channel_username = "data_ish"
    channel_name = "DATA | ISH"

    _FOOTER_MARKERS = ["@Data_bandlik", "@data_ish", "vakansiya joylash uchun"]

    def is_vacancy(self, message: dict) -> bool:
        text = message.get("raw_text", "")
        # Filter meta-posts
        if text.startswith("E'lon joylamoqchi"):
            return False
        # Must have at least one of: requirements, salary, or job invitation
        indicators = ["Talablar", "Талаблар", "ishga taklif", "ishga qabul", "📌", "vakansiya"]
        return any(ind in text for ind in indicators)

    def extract(self, message: dict) -> ParsedVacancy | None:
        text = message.get("raw_text", "")
        text_clean = self.clean_footer(text, self._FOOTER_MARKERS)

        lines = text_clean.split("\n")

        # Title: first non-empty line (usually contains job title + company intro)
        title = ""
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith(("📌", "✅", "❇️", "☎️", "📍", "👉")):
                title = stripped
                break

        if not title:
            return None

        # Company: often embedded in title line ("X kompaniyasiga Y kerak")
        company = self._extract_company(title)

        # Salary: look for "Maosh:" or "Маош:" pattern
        salary_text = self.get_field_value(text_clean, ["Maosh", "Маosh", "Маош"])
        sal_min, sal_max, sal_currency = self.extract_salary(salary_text)

        # Location
        location = self.get_field_value(text_clean, ["Manzil", "Манзил", "📍 Manzil", "📍 Манзил"])
        if not location:
            # Try lines starting with 📍
            for line in lines:
                if "📍" in line:
                    location = (
                        line.replace("📍", "").replace("Manzil:", "").replace("Манзил:", "").strip()
                    )
                    break

        # Work schedule
        self.get_field_value(text_clean, ["Ish vaqti", "Иш вақти", "График"])

        # Contact
        contact = ""
        for line in lines:
            if "☎️" in line or "Aloqa" in line:
                contact = self.extract_contacts(line)
                break
        if not contact:
            contact = self.extract_contacts(text_clean)

        return ParsedVacancy(
            title=title,
            description=text_clean,
            company=company,
            salary_min=sal_min,
            salary_max=sal_max,
            salary_currency=sal_currency,
            location=location,
            work_format=self.detect_work_format(text_clean),
            employment_type=self.detect_employment_type(text_clean),
            experience_years=self.extract_experience(text_clean),
            skills=self.extract_skills(text_clean),
            contact_info=contact,
            language="uz",
            posted_at=self._parse_date(message),
        )

    @staticmethod
    def _extract_company(title: str) -> str:
        """Try to extract company name from title like 'X kompaniyasiga Y kerak'."""
        # Pattern: "CompanyName" before keywords
        patterns = [
            r'^["\']?(.+?)["\']?\s+kompaniyasiga',
            r'^["\']?(.+?)["\']?\s+ga\s+',
            r"^💼\s*(.+?)\s+компаниясига",
        ]
        for p in patterns:
            match = re.search(p, title, re.IGNORECASE)
            if match:
                return match.group(1).strip().strip("\"'")
        return ""

    @staticmethod
    def _parse_date(message: dict):
        from datetime import datetime

        date_str = message.get("date")
        if date_str:
            try:
                return datetime.fromisoformat(date_str)
            except (ValueError, TypeError):
                pass
        return None
