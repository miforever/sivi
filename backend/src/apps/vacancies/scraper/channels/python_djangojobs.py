"""Parser for @python_djangojobs (Python Jobs) channel.

Format: Primarily Russian, hashtag-prefixed, colon-delimited sections.
Structure:
    #вакансия #python ...
    Job Title
    Company description
    Требования: / Requirements:
    Условия: / Benefits
    Contacts: @username / email / URL
    Footer
"""

import re

from apps.vacancies.scraper.channels.base import BaseChannelParser, ParsedVacancy


class PythonDjangoJobsParser(BaseChannelParser):
    channel_username = "python_djangojobs"
    channel_name = "Python Jobs"

    _FOOTER_MARKERS = ["👉 Подписаться", "Подписаться на канал"]

    _NON_VACANCY_KEYWORDS = [
        "Reklama kontenti",
        "reklama kontenti",
        "webinar",
        "kurs ",
        "intensiv",
        "Ramazon",
    ]

    _VACANCY_KEYWORDS = [
        "вакансия",
        "Вакансия",
        "требования",
        "Требования",
        "компания",
        "Компания",
        "зарплата",
        "Зарплата",
        "опыт",
        "kerak",
        "Maosh",
        "Talablar",
    ]

    def is_vacancy(self, message: dict) -> bool:
        text = message.get("raw_text", "")
        if any(kw in text for kw in self._NON_VACANCY_KEYWORDS):
            return False
        return sum(1 for kw in self._VACANCY_KEYWORDS if kw in text) >= 2

    def extract(self, message: dict) -> ParsedVacancy | None:
        text = message.get("raw_text", "")
        text_clean = self.clean_footer(text, self._FOOTER_MARKERS)

        lines = text_clean.split("\n")

        # Prefer explicit "Должность" field for title
        title = self.get_field_value(text_clean, ["Должность", "Позиция", "Position"])

        # Fallback: skip hashtag lines, find first content line
        if not title:
            for line in lines:
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                # Skip lines that are field labels (Компания:, Формат:, etc.)
                cleaned = re.sub(r"^[^\w\[«\"(]*", "", stripped)
                if re.match(
                    r"^(Компания|Формат|Занятость|ЗП|Зарплата|Локация|Контакт)\s*:",
                    cleaned,
                    re.IGNORECASE,
                ):
                    continue
                title = stripped
                break

        if not title:
            return None

        # Company
        company = self.get_field_value(text_clean, ["Компания", "Kompaniya", "Company"])

        # Salary
        salary_text = self.get_field_value(text_clean, ["Зарплата", "ЗП", "Зп", "Maosh", "Salary"])
        sal_min, sal_max, sal_currency = self.extract_salary(salary_text)

        # Location
        location = self.get_field_value(
            text_clean, ["Локация", "Локации", "Location", "Hudud", "Город"]
        )

        # Work format
        format_text = self.get_field_value(
            text_clean, ["Формат работы", "Формат", "Ish turi", "Format"]
        )
        work_format = self.detect_work_format(format_text or text_clean)

        # Contact
        contact = self.get_field_value(
            text_clean, ["Контакты", "Контакт", "Contact", "Откликнуться"]
        )
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
            language="ru",
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
