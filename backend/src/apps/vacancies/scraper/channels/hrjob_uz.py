"""Parser for @hrjobuz (HR job Uzbekistan) channel.

Real format examples:
    BI Group | Вакансия: HR-менеджер (Ташкент)

    BI Group - крупнейший инвестиционно-строительный холдинг...

    Что нужно делать:
    — ...

    Мы предлагаем:
    🏗 ...
    💳 Оклад+ бонусы

    Резюме отправляйте на Whatsapp: 8-707-661-01-43
    Либо в телеграм: @KazynaYes

    ---

    📣Ассистент HR / администратор офиса / рецепшионист📣

    🍔О компании👑
    Бургер Кинг в Узбекистане (франшиза Швейцария)

    По Задачам: ...
    Что предлагаем:
    Зарплата — обсуждается индивидуально
    Локация офиса по ул Бобура, 74
    График 5/2, 9.00-18.00
    📱 CV https://t.me/HR_S_Diyora
"""

import re

from apps.vacancies.scraper.channels.base import BaseChannelParser, ParsedVacancy


class HrjobUzParser(BaseChannelParser):
    channel_username = "hrjobuz"
    channel_name = "HR job Uzbekistan"

    _FOOTER_MARKERS = [
        "@hrjobuz",
        "HR job Uzbekistan",
    ]

    _AD_MARKERS = [
        "#реклама",
        "Подборка каналов",
        "курс по HR",
        "вебинар",
        "конференция",
    ]

    def is_vacancy(self, message: dict) -> bool:
        text = message.get("raw_text", "")
        if len(text) < 80:
            return False
        lower = text.lower()
        if any(m.lower() in lower for m in self._AD_MARKERS):
            return False
        indicators = [
            "вакансия",
            "требуется",
            "ищем",
            "требовани",
            "обязанност",
            "что нужно делать",
            "зарплата",
            "оклад",
            "з/п",
            "предлагаем",
            "резюме",
            "cv",
            "контакт",
            "график",
            "условия",
        ]
        matches = sum(1 for ind in indicators if ind in lower)
        return matches >= 2

    def extract(self, message: dict) -> ParsedVacancy | None:
        text = message.get("raw_text", "")
        text_clean = self.clean_footer(text, self._FOOTER_MARKERS)

        lines = text_clean.split("\n")

        # Prefer explicit "Должность" field for title
        title = self.get_field_value(text_clean, ["Должность", "Позиция"])

        # Fallback: first non-empty line, strip emoji and common prefixes
        if not title:
            for line in lines:
                stripped = line.strip()
                if not stripped or len(stripped) < 5:
                    continue
                cleaned = re.sub(r"^[^\w\[«\"(]*", "", stripped)
                # Handle "Company | Вакансия: Title" format
                if "Вакансия:" in cleaned:
                    cleaned = cleaned.split("Вакансия:")[-1].strip()
                elif "вакансия:" in cleaned.lower():
                    cleaned = re.split(r"(?i)вакансия\s*:\s*", cleaned)[-1].strip()
                if cleaned and len(cleaned) > 3:
                    title = cleaned
                    break

        if not title:
            return None

        # Company — company info section or "Company |" prefix in title
        company = ""
        company_match = re.search(
            r"О компании[^\n]*\n(.+?)(?:\n\n|\n[А-ЯA-Z])", text_clean, re.DOTALL
        )
        if company_match:
            company = company_match.group(1).strip().split("\n")[0].strip()
        if not company:
            # "BI Group | Вакансия:" → extract "BI Group"
            first_line = lines[0].strip() if lines else ""
            pipe_match = re.match(r"^[^\w]*([\w\s.&]+?)\s*\|\s*[Вв]акансия", first_line)
            if pipe_match:
                company = pipe_match.group(1).strip()
        if not company:
            company = self.get_field_value(text_clean, ["Компания", "Организация"])

        # Salary
        salary_text = self.get_field_value(
            text_clean,
            ["Зарплата", "Оклад", "З/п"],
        )
        if not salary_text:
            for line in lines:
                if re.search(r"зарплат|оклад|з/?п", line, re.IGNORECASE):
                    salary_text = line
                    break
        sal_min, sal_max, sal_currency = self.extract_salary(salary_text)

        # Location
        location = self.get_field_value(
            text_clean,
            ["Адрес", "Локация", "Местоположение"],
        )
        if not location:
            for line in lines:
                if re.search(r"Локация|📍|ул\s|улица|район", line, re.IGNORECASE):
                    location = re.sub(
                        r"^[^\w]*Локация[^\w]*", "", line, flags=re.IGNORECASE
                    ).strip()
                    if not location:
                        location = re.sub(r"^[^\w]*", "", line).strip()
                    break

        # Contact — "Резюме отправляйте" / "CV" / Telegram link
        contact = ""
        for line in lines:
            if re.search(r"резюме|cv|whatsapp|telegram|пиши", line, re.IGNORECASE):
                found = self.extract_contacts(line)
                if found:
                    contact = found
                    break
                # Check for URLs
                urls = self.extract_urls(line)
                if urls:
                    contact = urls[0]
                    break
        if not contact:
            contact = self.extract_contacts(text_clean)

        # Work schedule
        schedule = self.get_field_value(text_clean, ["График", "Режим"])
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
