"""Parser for @clozjobs (Tashkent Jobs) channel.

Format: Bilingual Uz/Ru, emoji-delimited fields.
Structure:
    Position Title (Uz / Ru)
    🏢 Company Name
    💰 Salary
    📞 Batafsil / Подробнее: URL
    ➖
    👉 Footer
"""

from apps.vacancies.scraper.channels.base import BaseChannelParser, ParsedVacancy


class ClozJobsParser(BaseChannelParser):
    channel_username = "clozjobs"
    channel_name = "Tashkent Jobs"

    _FOOTER_MARKERS = ["➖", "👉 Ish kanallari", "👉 Ko'proq ish", "👉 Больше вакансий"]

    def is_vacancy(self, message: dict) -> bool:
        text = message.get("raw_text", "")
        # All posts in this channel are vacancies; validate with URL pattern
        return "cloz.uz/vacansies/" in text or "📞" in text

    def extract(self, message: dict) -> ParsedVacancy | None:
        text = message.get("raw_text", "")
        text_clean = self.clean_footer(text, self._FOOTER_MARKERS)

        lines = [line.strip() for line in text_clean.split("\n") if line.strip()]
        if not lines:
            return None

        # Title is always the first non-empty line
        title = lines[0]

        # Company: line starting with 🏢
        company = ""
        for line in lines:
            if line.startswith("🏢"):
                company = line.lstrip("🏢").strip()
                break

        # Salary: line starting with 💰
        salary_text = ""
        for line in lines:
            if line.startswith("💰"):
                salary_text = line.lstrip("💰").strip()
                break
        sal_min, sal_max, sal_currency = self.extract_salary(salary_text)

        # URL from 📞 line
        source_url = ""
        urls = self.extract_urls(text)
        for url in urls:
            if "cloz.uz" in url:
                source_url = url
                break

        # Location: line starting with 📍 (rare)
        location = ""
        for line in lines:
            if line.startswith("📍"):
                location = line.lstrip("📍").strip()
                break

        return ParsedVacancy(
            title=title,
            description=text_clean,
            company=company,
            salary_min=sal_min,
            salary_max=sal_max,
            salary_currency=sal_currency,
            location=location or "Tashkent",
            language="uz/ru",
            source_url=source_url,
            skills=self.extract_skills(text_clean),
            work_format=self.detect_work_format(text_clean),
            contact_info=source_url,
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
