"""Parser for @edu_vakansiya (Edu Vakansiya) channel.

Format: Uzbek, highly consistent template.
Structure:
    ❇️ Job Title (gender) kerak
    Talablar: (— bullet points)
    Biz taklif qilamiz: (— bullet points)
    ➖Tashkilot: Name
    ➖Ish vaqti: Schedule
    ➖Maosh: Salary
    ➖Manzil: Location
    📞 Aloqa: phone
    📩 Forma: @handle
    👉@edu_vakansiya footer
"""

from apps.vacancies.scraper.channels.base import BaseChannelParser, ParsedVacancy


class EduVakansiyaParser(BaseChannelParser):
    channel_username = "edu_vakansiya"
    channel_name = "Edu Vakansiya"

    _FOOTER_MARKERS = ["👉@edu_vakansiya", "👉 @edu_vakansiya"]

    def is_vacancy(self, message: dict) -> bool:
        text = message.get("raw_text", "")
        return "kerak" in text.lower() or "Talablar" in text

    def extract(self, message: dict) -> ParsedVacancy | None:
        text = message.get("raw_text", "")
        text_clean = self.clean_footer(text, self._FOOTER_MARKERS)

        lines = text_clean.split("\n")

        # Title: first line, starts with ❇️
        title = ""
        for line in lines:
            stripped = line.strip()
            if stripped:
                title = stripped.lstrip("❇️").strip()
                break

        if not title:
            return None

        # Organization
        company = self.get_field_value(text_clean, ["Tashkilot"])

        # Salary
        salary_text = self.get_field_value(text_clean, ["Maosh"])
        sal_min, sal_max, sal_currency = self.extract_salary(salary_text)

        # Location
        location = self.get_field_value(text_clean, ["Manzil"])

        # Work schedule
        self.get_field_value(text_clean, ["Ish vaqti"])

        # Contact
        phone_line = self.get_field_value(text_clean, ["Aloqa"])
        form_line = self.get_field_value(text_clean, ["Forma"])
        contact_parts = [p for p in [phone_line, form_line] if p]
        contact = ", ".join(contact_parts)
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
            skills=self.extract_skills(text_clean),
            contact_info=contact,
            language="uz",
            work_format=self.detect_work_format(text_clean),
            employment_type=self.detect_employment_type(text_clean),
            experience_years=self.extract_experience(text_clean),
            posted_at=self._parse_date(message),
        )

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
