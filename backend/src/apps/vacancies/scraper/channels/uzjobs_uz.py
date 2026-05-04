"""Parser for @UzjobsUz channel.

Format: Highly standardized, bilingual En/Ru.
English pattern:
    Vacancy: Job Title
    https://uzjobs.uz/e/vakansy_view-XXXXX.html
    Company: Name
    Period of publication: DD.MM.YYYY - DD.MM.YYYY
    Region: Location
    Salary offered: ...

Russian pattern:
    Вакансия: Job Title
    https://uzjobs.uz/r/vakansy_view-XXXXX.html
    Компания: Name
    Период размещения: DD.MM.YYYY - DD.MM.YYYY
    Регион: Location
    Предлагаемая зарплата: ...
"""

from apps.vacancies.scraper.channels.base import BaseChannelParser, ParsedVacancy


class UzjobsUzParser(BaseChannelParser):
    channel_username = "UzjobsUz"
    channel_name = "UzJobs.uz"

    _NON_VACANCY_MARKERS = [
        "Дорогие друзья!",
        "UZUM TEZKOR",
        "Ramazon hayiti",
    ]

    def is_vacancy(self, message: dict) -> bool:
        text = message.get("raw_text", "")
        if any(m in text for m in self._NON_VACANCY_MARKERS):
            return False
        return "Vacancy:" in text or "Вакансия:" in text

    def extract(self, message: dict) -> ParsedVacancy | None:
        text = message.get("raw_text", "")

        # Posts come in En or Ru format — extract fields from both
        is_english = text.startswith("Vacancy:")

        if is_english:
            title = self.get_field_value(text, ["Vacancy"])
            company = self.get_field_value(text, ["Company"])
            location = self.get_field_value(text, ["Region"])
            salary_text = self.get_field_value(text, ["Salary offered"])
        else:
            title = self.get_field_value(text, ["Вакансия"])
            company = self.get_field_value(text, ["Компания"])
            location = self.get_field_value(text, ["Регион"])
            salary_text = self.get_field_value(text, ["Предлагаемая зарплата"])

        if not title:
            return None

        sal_min, sal_max, sal_currency = self.extract_salary(salary_text)

        # Extract URL
        source_url = ""
        urls = self.extract_urls(text)
        for url in urls:
            if "uzjobs.uz" in url:
                source_url = url
                break

        return ParsedVacancy(
            title=title,
            description=text,
            company=company,
            salary_min=sal_min,
            salary_max=sal_max,
            salary_currency=sal_currency,
            location=location,
            language="",
            source_url=source_url,
            skills=self.extract_skills(text),
            work_format=self.detect_work_format(text),
            employment_type=self.detect_employment_type(text),
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
