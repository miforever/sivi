"""Parser for @uzbekistanishborwork (TashJob - Uzbekistan ishbor) channel.

Real format examples:
    [Вакансия] Медицинский представитель

    Компания: ASKLEPIY Group

    Требования:
    - ...

    Обязанности:
    - ...

    Условия:
    - ...

    Оплата: по итогам собеседования

    Хотите уточнить актуальность вакансий?
    Свяжитесь с — @handle
    ➖➖➖➖➖➖

    ---

    🆕ВАКАНСИЯ: МЕНЕДЖЕР ПО ПОИСКУ КЛИЕНТОВ (B2B)
    ...

Ads to skip: personal stories, motivational posts, channel promos
"""

import re

from apps.vacancies.scraper.channels.base import BaseChannelParser, ParsedVacancy


class UzbekistanIshborParser(BaseChannelParser):
    channel_username = "uzbekistanishborwork"
    channel_name = "TashJob - Uzbekistan ishbor"

    _FOOTER_MARKERS = [
        "➖➖",
        "Хотите уточнить актуальность",
        "@uzbekistanishborwork",
    ]

    _AD_MARKERS = [
        "лет назад я сидела",
        "Регистрационный номер",
        "ИП №",
        "Построй карьеру",
        "Подборка каналов",
        "#реклама",
    ]

    def is_vacancy(self, message: dict) -> bool:
        text = message.get("raw_text", "")
        if len(text) < 80:
            return False
        lower = text.lower()
        # Reject ads / personal stories
        if any(m.lower() in lower for m in self._AD_MARKERS):
            return False
        # Must have "[Вакансия]" or "ВАКАНСИЯ:" or job indicators
        indicators = [
            "[вакансия]",
            "вакансия:",
            "требования",
            "обязанности",
            "оплата",
            "зарплата",
            "компания:",
            "свяжитесь",
            "требуется",
            "ищем",
            "приглашает в команду",
        ]
        matches = sum(1 for ind in indicators if ind in lower)
        return matches >= 2

    def extract(self, message: dict) -> ParsedVacancy | None:
        text = message.get("raw_text", "")
        text_clean = self.clean_footer(text, self._FOOTER_MARKERS)

        lines = text_clean.split("\n")

        # Prefer explicit "Должность" field for title
        title = self.get_field_value(text_clean, ["Должность", "Позиция"])

        # Fallback: "[Вакансия] Title" or "🆕ВАКАНСИЯ: Title" or first line
        if not title:
            for line in lines:
                stripped = line.strip()
                if not stripped or len(stripped) < 5:
                    continue
                # Remove [Вакансия] / ВАКАНСИЯ: prefix and leading emojis
                cleaned = re.sub(r"^[^\w\[]*", "", stripped)
                cleaned = re.sub(r"^\[Вакансия\]\s*", "", cleaned, flags=re.IGNORECASE)
                cleaned = re.sub(r"^ВАКАНСИЯ\s*:\s*", "", cleaned, flags=re.IGNORECASE)
                if cleaned and len(cleaned) > 3:
                    title = cleaned
                    break

        if not title:
            return None

        # Company
        company = self.get_field_value(
            text_clean,
            ["Компания", "Организация"],
        )

        # Salary
        salary_text = self.get_field_value(
            text_clean,
            ["Оплата", "Зарплата", "Оклад", "З/п"],
        )
        sal_min, sal_max, sal_currency = self.extract_salary(salary_text)

        # Location
        location = self.get_field_value(
            text_clean,
            ["Адрес", "Локация", "Место", "Район"],
        )
        if not location:
            for line in lines:
                if "📍" in line:
                    location = re.sub(r"^[^\w]*", "", line).strip()
                    break

        # Contact — "@handle" or phone
        contact = ""
        for line in lines:
            if "Свяжитесь" in line or "свяжитесь" in line:
                contact = self.extract_contacts(line)
                break
        if not contact:
            contact = self.get_field_value(
                text_clean,
                ["Контакт", "Телефон", "Связь"],
            )
        if not contact:
            contact = self.extract_contacts(text_clean)

        # Work schedule
        schedule = self.get_field_value(text_clean, ["График"])
        work_format = self.detect_work_format(schedule or text_clean)

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
