"""Parser for @ITjobs_Uzbekistan (Uzbekistan IT Jobs) channel.

Very consistent format:
    #Web #Разработчик #WebРазработчик
    #C (от 500$ и выше)

    🏢Компания:  OOO «Wind Lace»
    Должность:  Web Разработчик
    Занятость Полная занятость
    Знания языков: ...

    🔻Обязанности:
    - ...

    🔻Основные требования:
    - ...

    Дополнительно:
    - ...

    📱Контакт: @handle (Name)

    🆔 #itjobNNN
    @ITjobs_Uzbekistan
"""

import re

from apps.vacancies.scraper.channels.base import BaseChannelParser, ParsedVacancy


class ITjobsUzbekistanParser(BaseChannelParser):
    channel_username = "ITjobs_Uzbekistan"
    channel_name = "Uzbekistan IT Jobs"

    _FOOTER_MARKERS = [
        "🆔",
        "@ITjobs_Uzbekistan",
    ]

    def is_vacancy(self, message: dict) -> bool:
        text = message.get("raw_text", "")
        if len(text) < 50:
            return False
        # Very reliable: posts have 🏢Компания or Должность or #C (salary)
        return "🏢" in text or "Должность" in text or "#C " in text

    def extract(self, message: dict) -> ParsedVacancy | None:
        text = message.get("raw_text", "")
        text_clean = self.clean_footer(text, self._FOOTER_MARKERS)

        # Title from "Должность:" field, fallback to first hashtag line
        title = self.get_field_value(text_clean, ["Должность"])
        if not title:
            # First line is usually hashtags — not great for title
            # Try to build from hashtags
            first_line = text_clean.split("\n")[0].strip()
            if first_line.startswith("#"):
                # Clean hashtags: "#Web #Разработчик" → "Web Разработчик"
                title = re.sub(r"#", "", first_line).strip()
            else:
                title = first_line

        if not title:
            return None

        # Company from "🏢Компания:" — handle emoji prefix
        company = ""
        for line in text_clean.split("\n"):
            if "Компания" in line:
                company = re.sub(r"^[^\w]*Компания\s*:\s*", "", line).strip()
                break

        # Salary from "#C (...)" or "#AA (...)" or "#A (...)" tags
        salary_text = ""
        sal_match = re.search(r"#[A-Z]+\s*\((.+?)\)", text_clean)
        if sal_match:
            salary_text = sal_match.group(1)
        sal_min, sal_max, sal_currency = self.extract_salary(salary_text)

        # Location from 📍 line
        location = ""
        for line in text_clean.split("\n"):
            if "📍" in line:
                location = re.sub(r"^[^\w]*", "", line).strip()
                break

        # Contact from "📱Контакт:" line
        contact = ""
        for line in text_clean.split("\n"):
            if "Контакт" in line:
                contact = re.sub(r"^[^\w]*Контакт\s*:\s*", "", line).strip()
                break
        if not contact:
            contact = self.extract_contacts(text_clean)

        # Employment type from "Занятость" line
        emp_text = self.get_field_value(text_clean, ["Занятость"])
        employment_type = self.detect_employment_type(emp_text or text_clean)

        return ParsedVacancy(
            title=title,
            description=text_clean,
            company=company,
            salary_min=sal_min,
            salary_max=sal_max,
            salary_currency=sal_currency,
            location=location,
            work_format=self.detect_work_format(text_clean),
            employment_type=employment_type,
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
