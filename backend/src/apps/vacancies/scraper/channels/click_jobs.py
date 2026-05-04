"""Parser for @click_jobs (Click Jobs) channel.

Format: Uzbek, em-dash delimited, very consistent.
Structure:
    Job Title kerak!
    — Ish holati: #aktiv
    — Kompaniya: Name
    — Kompaniya haqida: Description
    — Hudud: Location
    — Ish turi: Oflayn/Online
    — Maosh: Salary
    — Talablar: Requirements (can be multi-line with •)
    — Murojaat uchun: @handle
    @click_jobs footer
"""

from apps.vacancies.scraper.channels.base import BaseChannelParser, ParsedVacancy


class ClickJobsParser(BaseChannelParser):
    channel_username = "click_jobs"
    channel_name = "Click Jobs"

    _FOOTER_MARKERS = [
        "@click_jobs —",
        "@click_jobs —",
        "Kanalda e'lon joylash",
    ]

    def is_vacancy(self, message: dict) -> bool:
        text = message.get("raw_text", "")
        return "Ish holati:" in text or ("kerak" in text.lower() and "Murojaat" in text)

    def extract(self, message: dict) -> ParsedVacancy | None:
        text = message.get("raw_text", "")
        text_clean = self.clean_footer(text, self._FOOTER_MARKERS)

        lines = text_clean.split("\n")

        # Title: first non-empty line
        title = ""
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith("—"):
                title = stripped
                break

        if not title:
            return None

        # Company
        company = self.get_field_value(text_clean, ["Kompaniya"])
        # Don't capture "Kompaniya haqida" as company name
        company_about = self.get_field_value(text_clean, ["Kompaniya haqida"])
        if company == company_about and company_about:
            company = ""

        # Salary
        salary_text = self.get_field_value(text_clean, ["Maosh"])
        sal_min, sal_max, sal_currency = self.extract_salary(salary_text)

        # Location
        location = self.get_field_value(text_clean, ["Hudud"])

        # Work type
        work_type = self.get_field_value(text_clean, ["Ish turi"])
        work_format = self.detect_work_format(work_type)

        # Requirements (may be multi-line with bullet points)
        self.get_field_value(text_clean, ["Talablar"])

        # Contact
        contact = self.get_field_value(text_clean, ["Murojaat uchun"])
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
            work_format=work_format,
            employment_type=self.detect_employment_type(text_clean),
            experience_years=self.extract_experience(text_clean),
            skills=self.extract_skills(text_clean),
            contact_info=contact,
            language="uz",
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
