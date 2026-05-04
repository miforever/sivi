"""Parser for @vacancyuzairports (Vacancy Uzbekistan Airports) channel.

Format: Uzbek / Russian, aviation and transport sector jobs.
Large channel (~39.6k). No real samples yet — using generic Uz/Ru parser
with aviation-specific ad filtering.
"""

import re

from apps.vacancies.scraper.channels.base import BaseChannelParser, ParsedVacancy


class VacancyUzAirportsParser(BaseChannelParser):
    channel_username = "vacancyuzairports"
    channel_name = "Vacancy Uzbekistan Airports"

    _FOOTER_MARKERS = [
        "➖➖",
        "@vacancyuzairports",
    ]

    _AD_MARKERS = [
        "расписание рейсов",
        "parvoz jadvali",
        "задержка рейса",
        "новый маршрут",
        "yangi yo'nalish",
        "#реклама",
        "авиабилет",
        "бронирова",
    ]

    def is_vacancy(self, message: dict) -> bool:
        text = message.get("raw_text", "")
        if len(text) < 60:
            return False
        lower = text.lower()
        if any(m in lower for m in self._AD_MARKERS):
            return False
        indicators = [
            "вакансия",
            "vakansiya",
            "vacancy",
            "требуется",
            "kerak",
            "ищем",
            "талаблар",
            "talablar",
            "требовани",
            "обязанност",
            "маош",
            "maosh",
            "зарплата",
            "salary",
            "оклад",
            "murojaat",
            "мурожаат",
            "обращаться",
            "контакт",
            "резюме",
            "ishga",
            "ишга",
        ]
        matches = sum(1 for ind in indicators if ind in lower)
        return matches >= 2

    def extract(self, message: dict) -> ParsedVacancy | None:
        text = message.get("raw_text", "")
        text_clean = self.clean_footer(text, self._FOOTER_MARKERS)

        lines = text_clean.split("\n")

        # Title: first non-empty line, strip emojis and "Вакансия:" prefix
        title = ""
        for line in lines:
            stripped = line.strip()
            if not stripped or len(stripped) < 5:
                continue
            cleaned = re.sub(r"^[^\w\[«\"(]*", "", stripped)
            cleaned = re.sub(r"^[Вв]акансия\s*:\s*", "", cleaned)
            cleaned = re.sub(r"^[Vv]akansiya\s*:\s*", "", cleaned)
            if cleaned and len(cleaned) > 3:
                title = cleaned
                break

        if not title:
            return None

        # Company / Organization
        company = self.get_field_value(
            text_clean,
            [
                "Компания",
                "Организация",
                "Ташкилот",
                "Tashkilot",
                "Kompaniya",
                "Аэропорт",
                "Aeroport",
            ],
        )

        # Salary
        salary_text = self.get_field_value(
            text_clean,
            ["Маош", "Maosh", "Зарплата", "Salary", "Oylik", "Оклад"],
        )
        sal_min, sal_max, sal_currency = self.extract_salary(salary_text)

        # Location
        location = self.get_field_value(
            text_clean,
            ["Манзил", "Manzil", "Адрес", "Локация", "Худуд", "Hudud"],
        )
        if not location:
            for line in lines:
                if "📍" in line:
                    location = re.sub(r"^[^\w]*", "", line).strip()
                    break

        # Source URL
        source_url = ""
        urls = self.extract_urls(text_clean)
        for url in urls:
            if "t.me" not in url:
                source_url = url
                break

        # Contact
        contact = self.get_field_value(
            text_clean,
            ["Murojaat", "Мурожаат", "Обращаться", "Контакт", "Aloqa", "Телефон", "Резюме"],
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
            work_format=self.detect_work_format(text_clean),
            employment_type=self.detect_employment_type(text_clean),
            experience_years=self.extract_experience(text_clean),
            skills=self.extract_skills(text_clean),
            contact_info=contact,
            source_url=source_url,
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
