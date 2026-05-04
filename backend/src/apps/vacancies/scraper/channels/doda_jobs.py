"""Parser for @doda_jobs (Doda Jobs - Работа в Ташкенте) channel.

Real format examples:
    🟥 Вакансия: Заведующий складом (автозапчасти спец.техники)
    ❤️Заработная плата: от 6 000 000 – 7 000 000 сум + бонусы
    🔽 Обязанности: ...
    🔽 Требования: ...
    🔽 Условия: ...
    📌Адрес: г. Ташкент, ...
    💬Резюме в Telegram: +998...

    ---

    📣 В магазин ... требуется Позитивная продавец
    😀 Требования: ...
    ↖️Ориентир м.Космонавтов.
    💳 З/п при собеседовании.
    🩵 Фото и резюме высылать по номеру ...

Ads to skip: flight promos, channel lists, #реклама
"""

import re

from apps.vacancies.scraper.channels.base import BaseChannelParser, ParsedVacancy


class DodaJobsParser(BaseChannelParser):
    channel_username = "doda_jobs"
    channel_name = "Doda Jobs"

    _FOOTER_MARKERS = [
        "➖➖",
        "@Doda_Jobs",
        "@doda_jobs",
    ]

    _AD_MARKERS = [
        "#реклама",
        "Подборка Telegram-каналов",
        "Подборка каналов",
        "Прямой рейс",
        "авиабилет",
        "Забронировать",
        "centrum-air",
    ]

    def is_vacancy(self, message: dict) -> bool:
        text = message.get("raw_text", "")
        if len(text) < 80:
            return False
        lower = text.lower()
        # Reject ads
        if any(m.lower() in lower for m in self._AD_MARKERS):
            return False
        # Must have at least 2 of these job indicators
        indicators = [
            "вакансия",
            "требуется",
            "требования",
            "обязанности",
            "зарплат",
            "заработн",
            "з/п",
            "оклад",
            "резюме",
            "контакт",
            "обращаться",
            "telegram",
            "график",
            "условия",
        ]
        matches = sum(1 for ind in indicators if ind in lower)
        return matches >= 2

    def extract(self, message: dict) -> ParsedVacancy | None:
        text = message.get("raw_text", "")
        text_clean = self.clean_footer(text, self._FOOTER_MARKERS)

        lines = text_clean.split("\n")

        # Company — extract before title so we can skip "Компания:" lines
        company = ""
        for line in lines:
            cleaned_line = re.sub(r"^[^\w]*", "", line.strip())
            if re.match(r"Компания\s*:", cleaned_line, re.IGNORECASE):
                company = re.sub(r"^Компания\s*:\s*", "", cleaned_line, flags=re.IGNORECASE).strip()
                break
        if not company:
            company = self.get_field_value(text_clean, ["Компания", "Организация"])

        # Prefer explicit "Должность" field for title
        title = self.get_field_value(text_clean, ["Должность", "Позиция"])

        # Fallback: first non-empty line that isn't a field label
        field_prefixes = re.compile(
            r"^(Компания|Зарплат|Заработн|Оклад|З/?п|Требовани|Обязанност|Условия|Адрес|График|Резюме|Контакт|Должность|Формат|Занятость)\s*:",
            re.IGNORECASE,
        )
        if not title:
            for line in lines:
                stripped = line.strip()
                if not stripped or len(stripped) < 5:
                    continue
                # Strip leading emojis
                cleaned = re.sub(r"^[^\w\[«\"(]*", "", stripped)
                # Skip field label lines
                if field_prefixes.match(cleaned):
                    continue
                cleaned = re.sub(r"^Вакансия\s*:\s*", "", cleaned, flags=re.IGNORECASE)
                if cleaned and len(cleaned) > 3:
                    title = cleaned
                    break

        if not title:
            return None

        # Salary — multiple label variants
        salary_text = self.get_field_value(
            text_clean,
            ["Заработная плата", "Зарплата", "Оклад", "З/п"],
        )
        if not salary_text:
            # Try salary shorthand lines
            for line in lines:
                if re.search(r"з/?п|зарплат|заработн|оклад", line, re.IGNORECASE):
                    salary_text = line
                    break
        sal_min, sal_max, sal_currency = self.extract_salary(salary_text)

        # Location
        location = self.get_field_value(
            text_clean,
            ["Адрес", "Локация", "Район", "Ориентир"],
        )
        if not location:
            for line in lines:
                if "📍" in line or "Ориентир" in line or "↖️" in line:
                    location = re.sub(r"^[^\w]*", "", line).strip()
                    location = re.sub(r"^Ориентир\s*", "", location, flags=re.IGNORECASE)
                    break

        # Contact — look for Telegram/phone in "Резюме" lines
        contact = self.get_field_value(
            text_clean,
            ["Резюме", "Контакт", "Обращаться", "Телефон", "Связь"],
        )
        if not contact:
            contact = self.extract_contacts(text_clean)

        # Work schedule
        schedule = self.get_field_value(text_clean, ["График", "Режим работы"])
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
