"""Parser for @Exampleuz (Example.uz - IT Jobs) channel.

Format: Highly variable — 3 sub-formats by post structure.
  A) Uzbek-style: em-dash metadata fields (like click_jobs)
  B) Emoji-section headers (💼 📌 ✅ 🎁) with Ru field names
  C) Narrative with dash bullet points and En field names

All share:
  - Hashtags for categorization
  - ⭐️ separator before footer
  - Footer: 👉 @jakhongir095 / @Exampleuz
"""

import re

from apps.vacancies.scraper.channels.base import BaseChannelParser, ParsedVacancy


class ExampleUzParser(BaseChannelParser):
    channel_username = "Exampleuz"
    channel_name = "Example.uz - IT Jobs"

    _FOOTER_MARKERS = [
        "⭐️⭐️",
        "👉 Vakansiya, Resume",
        "👉 For Vacancies",
        "Har kunlik e'lonlar",
        "Subscribe for daily",
    ]

    def is_vacancy(self, message: dict) -> bool:
        text = message.get("raw_text", "")
        indicators = [
            "kerak",
            "Talablar",
            "Требования",
            "Requirements",
            "Maosh",
            "Зарплата",
            "Salary",
            "Murojaat",
            "Откликнуться",
            "reach out",
            "Kompaniya",
            "Компания",
            "#aktiv",
        ]
        return sum(1 for ind in indicators if ind in text) >= 2

    def extract(self, message: dict) -> ParsedVacancy | None:
        text = message.get("raw_text", "")
        text_clean = self.clean_footer(text, self._FOOTER_MARKERS)

        # Choose extraction strategy based on post structure
        if self._is_emoji_section_format(text_clean):
            return self._extract_emoji_sections(text_clean, message)
        elif self._is_narrative_format(text_clean):
            return self._extract_narrative(text_clean, message)
        return self._extract_field_based(text_clean, message)

    def _extract_field_based(self, text: str, message: dict) -> ParsedVacancy | None:
        """Field-based format: em-dash/colon delimited metadata fields."""
        lines = text.split("\n")

        title = ""
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith(("—", "#", "📌")):
                title = stripped
                break

        if not title:
            return None

        company = self.get_field_value(text, ["Kompaniya"])
        salary_text = self.get_field_value(text, ["Maosh"])
        sal_min, sal_max, sal_currency = self.extract_salary(salary_text)
        location = self.get_field_value(text, ["Hudud", "Ish turi"])
        contact = self.get_field_value(text, ["Murojaat uchun"])
        if not contact:
            contact = self.extract_contacts(text)

        return ParsedVacancy(
            title=title,
            description=text,
            company=company,
            salary_min=sal_min,
            salary_max=sal_max,
            salary_currency=sal_currency,
            location=location,
            work_format=self.detect_work_format(text),
            employment_type=self.detect_employment_type(text),
            experience_years=self.extract_experience(text),
            skills=self.extract_skills(text),
            contact_info=contact,
            language="",
            posted_at=self._parse_date(message),
        )

    def _extract_emoji_sections(self, text: str, message: dict) -> ParsedVacancy | None:
        """Emoji-section format: headers like 💼 📌 ✅ 🎁."""
        # Title after 💼 or first bold line
        title = ""
        for line in text.split("\n"):
            stripped = line.strip()
            if stripped.startswith("💼"):
                title = stripped.lstrip("💼").strip()
                break
            if stripped and not stripped.startswith("#"):
                title = stripped
                break

        if not title:
            return None

        salary_text = self.get_field_value(text, ["Зарплата", "💰 Зарплата"])
        sal_min, sal_max, sal_currency = self.extract_salary(salary_text)

        location = self.get_field_value(text, ["Адрес", "📍 Адрес", "Город"])
        self.get_field_value(text, ["График", "🕐 График"])
        format_text = self.get_field_value(text, ["Формат работы", "💻 Формат работы"])
        contact = self.extract_contacts(text)

        return ParsedVacancy(
            title=title,
            description=text,
            company=self._extract_company_from_title(title),
            salary_min=sal_min,
            salary_max=sal_max,
            salary_currency=sal_currency,
            location=location,
            work_format=self.detect_work_format(format_text or text),
            employment_type=self.detect_employment_type(text),
            experience_years=self.extract_experience(text),
            skills=self.extract_skills(text),
            contact_info=contact,
            language="",
            posted_at=self._parse_date(message),
        )

    def _extract_narrative(self, text: str, message: dict) -> ParsedVacancy | None:
        """Narrative format: prose with dash bullet points."""
        lines = text.split("\n")

        title = ""
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                title = stripped
                break

        if not title:
            return None

        salary_text = self.get_field_value(text, ["Salary"])
        sal_min, sal_max, sal_currency = self.extract_salary(salary_text)
        contact = self.extract_contacts(text)

        # Location often on its own line
        location = ""
        location_keywords = ["Tashkent", "Remote", "Hybrid"]
        for line in lines:
            stripped = line.strip()
            if stripped in location_keywords or any(kw in stripped for kw in location_keywords):
                if len(stripped) < 50:  # Avoid grabbing long description lines
                    location = stripped
                    break

        return ParsedVacancy(
            title=title,
            description=text,
            company=self._extract_company_from_title(title),
            salary_min=sal_min,
            salary_max=sal_max,
            salary_currency=sal_currency,
            location=location,
            work_format=self.detect_work_format(text),
            employment_type=self.detect_employment_type(text),
            experience_years=self.extract_experience(text),
            skills=self.extract_skills(text),
            contact_info=contact,
            language="",
            posted_at=self._parse_date(message),
        )

    @staticmethod
    def _is_emoji_section_format(text: str) -> bool:
        """Check if text uses emoji-section headers (💼, 📌, ✅)."""
        return any(marker in text for marker in ("💼", "📌 ", "✅ "))

    @staticmethod
    def _is_narrative_format(text: str) -> bool:
        """Check if text uses narrative style with English field names."""
        return any(kw in text for kw in ("Salary", "Requirements:", "Experience:"))

    @staticmethod
    def _extract_company_from_title(title: str) -> str:
        """Extract company from titles like 'Role в CompanyName' or 'Role (Company)'."""
        # "в CompanyName" / "in CompanyName"
        match = re.search(r"(?:в|in|at)\s+(?:IT\s+company\s+)?(.+?)(?:\s*\(|$)", title)
        if match:
            return match.group(1).strip()
        # "(CompanyName)"
        match = re.search(r"\(([^)]+)\)", title)
        if match:
            return match.group(1).strip()
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
