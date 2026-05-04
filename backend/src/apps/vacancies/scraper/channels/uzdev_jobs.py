"""Parser for @uzdev_jobs (UzDev Jobs - IT Jobs) channel.

Format: Multi-language (Uz/Ru/En), hashtag-prefixed, colon-delimited fields.
Three sub-formats:
  A) Uzbek: "Kompaniya : Value" with space around colon
  B) Russian: "Вакансия: Value" with colon
  C) English: Narrative with dash bullet points
"""

import re

from apps.vacancies.scraper.channels.base import BaseChannelParser, ParsedVacancy


class UzdevJobsParser(BaseChannelParser):
    channel_username = "uzdev_jobs"
    channel_name = "UzDev Jobs – IT Jobs"

    _FOOTER_MARKERS = ["👉 Подписаться на канал", "👉 @UzDev_Jobs"]

    _AD_KEYWORDS = [
        "Reklama kontenti",
        "reklama kontenti",
        "Ramazon hayiti muborak",
        "ta'lim texnologiyalari",
    ]

    def is_vacancy(self, message: dict) -> bool:
        text = message.get("raw_text", "")
        # Filter ads and holiday greetings
        if any(kw in text for kw in self._AD_KEYWORDS):
            return False
        # Must have at least some job indicators
        job_indicators = [
            "#",
            "Kompaniya",
            "Компания",
            "Company",
            "Maosh",
            "Зарплата",
            "Salary",
            "Talablar",
            "Требования",
            "Requirements",
            "kerak",
            "ищем",
            "looking for",
        ]
        return any(ind in text for ind in job_indicators)

    def extract(self, message: dict) -> ParsedVacancy | None:
        text = message.get("raw_text", "")
        text_clean = self.clean_footer(text, self._FOOTER_MARKERS)

        lines = text_clean.split("\n")

        # Extract hashtags from first lines
        hashtags = []
        title_start = 0
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("#"):
                hashtags.extend(re.findall(r"#(\w+)", stripped))
                title_start = i + 1
            elif stripped:
                break

        # Prefer explicit "Должность" / "Lavozim" field for title
        title = self.get_field_value(text_clean, ["Должность", "Позиция", "Lavozim", "Position"])

        # Fallback: first non-hashtag, non-empty line
        if not title:
            for i in range(title_start, len(lines)):
                stripped = lines[i].strip()
                if stripped:
                    title = stripped
                    break

        if not title:
            return None

        # Company
        company = self.get_field_value(text_clean, ["Kompaniya", "Компания", "Company"])

        # Salary
        salary_text = self.get_field_value(
            text_clean, ["Maosh", "Ish haqi", "Зарплата", "ЗП", "Salary"]
        )
        sal_min, sal_max, sal_currency = self.extract_salary(salary_text)

        # Location
        location = self.get_field_value(
            text_clean, ["Joylashuv", "Manzil", "Локации", "Location", "Hudud"]
        )

        # Work format
        work_type_text = self.get_field_value(text_clean, ["Ish turi", "Формат работы", "Format"])
        work_format = self.detect_work_format(work_type_text or text_clean)

        # Requirements section for description richness
        self.get_section_content(text_clean, ["Talablar", "Требования", "Requirements"])

        # Contact
        contact = self.get_field_value(
            text_clean,
            [
                "Rezyume bilan murojaat qiling",
                "Murojaat uchun",
                "Контакты",
                "Contact",
                "Telegram",
                "Телеграмм",
            ],
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
            language="",
            source_url="",
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
