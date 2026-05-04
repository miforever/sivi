"""Parser for @UstozShogird channel.

Format: Uzbek (Latin), emoji+label fields, 5 post types.
Structure:
    [Post Type]: "Ish joyi kerak:", "Xodim kerak:", etc.
    👨‍💼 Xodim: Name
    📚 Texnologiya: skills
    💰 Narxi: salary
    🌐 Hudud: location
    👨🏻‍💻 Kasbi: position
    🔎 Maqsad: description
    #hashtags
    👉 @UstozShogird footer
"""

import re

from apps.vacancies.scraper.channels.base import BaseChannelParser, ParsedVacancy


class UstozShogirdParser(BaseChannelParser):
    channel_username = "UstozShogird"
    channel_name = "Ustoz-Shogird"

    _VACANCY_HEADERS = [
        "Xodim kerak",
        "Shogird kerak",
        "Ustoz kerak",
    ]

    _ANNOUNCEMENT_MARKERS = [
        "Ish e'lonlari joylashda muhim qoidalar",
        "Assalomu alaykum hurmatli kanalimiz",
        "Ko'p so'raladigan savollar",
    ]

    _FOOTER_MARKERS = ["👉 @UstozShogird"]

    def is_vacancy(self, message: dict) -> bool:
        text = message.get("raw_text", "")
        if any(m in text for m in self._ANNOUNCEMENT_MARKERS):
            return False
        return any(h in text for h in self._VACANCY_HEADERS)

    def extract(self, message: dict) -> ParsedVacancy | None:
        text = message.get("raw_text", "")
        text_clean = self.clean_footer(text, self._FOOTER_MARKERS)

        # Remove hashtag lines
        text_clean = re.sub(r"^#.*$", "", text_clean, flags=re.MULTILINE).strip()

        fields = self._extract_emoji_fields(text_clean)

        # Determine post type and build title
        post_type = ""
        for header in self._VACANCY_HEADERS:
            if header in text:
                post_type = header
                break

        position = fields.get("Kasbi", "")
        title = position or post_type
        if not title:
            return None

        # Tech/skills
        tech = fields.get("Texnologiya", "")
        skills = self.extract_skills(tech) if tech else self.extract_skills(text_clean)

        # Salary
        salary_text = fields.get("Narxi", "") or fields.get("Maosh", "")
        sal_min, sal_max, sal_currency = self.extract_salary(salary_text)

        # Contact
        telegram = fields.get("Telegram", "")
        phone = fields.get("Aloqa", "")
        contact_parts = [p for p in [telegram, phone] if p]
        contact_info = ", ".join(contact_parts)

        # Description from Maqsad or Qo`shimcha
        description = fields.get("Maqsad", "") or fields.get("Qo`shimcha", "")
        if not description:
            description = text_clean

        return ParsedVacancy(
            title=title,
            description=description,
            company=fields.get("Idora", ""),
            salary_min=sal_min,
            salary_max=sal_max,
            salary_currency=sal_currency,
            location=fields.get("Hudud", ""),
            skills=skills,
            contact_info=contact_info,
            language="uz",
            employment_type=self.detect_employment_type(text_clean),
            work_format=self.detect_work_format(text_clean),
            experience_years=self.extract_experience(text_clean),
            posted_at=self._parse_date(message),
        )

    @staticmethod
    def _extract_emoji_fields(text: str) -> dict[str, str]:
        """Extract fields delimited by emoji + label: value pattern."""
        fields = {}
        # Match lines like: 👨‍💼 Xodim: Jamshid
        # Emoji can be complex (ZWJ sequences), so match any non-ASCII prefix
        pattern = re.compile(
            r"^[^\w\n]*\s*([A-Za-zА-Яа-яʻʼ''`]+(?:\s+[A-Za-zА-Яа-яʻʼ''`]+)*)\s*:\s*(.+)$",
            re.MULTILINE,
        )
        for match in pattern.finditer(text):
            label = match.group(1).strip()
            value = match.group(2).strip()
            fields[label] = value
        return fields

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
