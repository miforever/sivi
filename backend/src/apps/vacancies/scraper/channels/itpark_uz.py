"""Parser for @itpark_uz (IT Park Uzbekistan) channel.

This channel is mostly news, events, and announcements — very few actual vacancies.
Need very strict filtering to only capture real job postings and skip:
- Certification programs, hackathons, bootcamps
- News about IT Park residents
- Event announcements
- Partnership/grant announcements

Only real vacancy posts should pass through.
"""

import re

from apps.vacancies.scraper.channels.base import BaseChannelParser, ParsedVacancy


class ItparkUzParser(BaseChannelParser):
    channel_username = "itpark_uz"
    channel_name = "IT Park Uzbekistan"

    _FOOTER_MARKERS = [
        "@itpark_uz",
        "IT Park Uzbekistan",
    ]

    _NOT_VACANCY = [
        "sertifikat",
        "certificate",
        "championship",
        "hackathon",
        "xakaton",
        "bootcamp",
        "kurs",
        "course",
        "meetup",
        "webinar",
        "vebinar",
        "tadbirga",
        "tadbir",
        "мероприятие",
        "конференция",
        "конкурс",
        "грант",
        "стипенди",
        "grant",
        "ishtirok eting",
        "ro'yxatdan o'ting",  # "participate", "register"
        "musobaqa",
        "competition",
        "tenderga",
        "tender",
        "#реклама",
    ]

    def is_vacancy(self, message: dict) -> bool:
        text = message.get("raw_text", "")
        if len(text) < 80:
            return False
        lower = text.lower()
        # Reject non-vacancy content (events, news, courses, etc.)
        if any(m in lower for m in self._NOT_VACANCY):
            return False
        # Must have strong vacancy signals
        indicators = [
            "вакансия",
            "vakansiya",
            "vacancy",
            "требуется",
            "kerak",
            "ищем",
            "developer",
            "dasturchi",
            "разработчик",
            "маош",
            "maosh",
            "зарплата",
            "salary",
            "талаблар",
            "talablar",
            "требовани",
            "murojaat",
            "мурожаат",
            "обращаться",
            "контакт",
        ]
        matches = sum(1 for ind in indicators if ind in lower)
        return matches >= 3  # Strict: need 3+ indicators

    def extract(self, message: dict) -> ParsedVacancy | None:
        text = message.get("raw_text", "")
        text_clean = self.clean_footer(text, self._FOOTER_MARKERS)

        lines = text_clean.split("\n")

        # Title
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

        # Company
        company = self.get_field_value(
            text_clean,
            ["Компания", "Kompaniya", "Company", "Ташкилот", "Tashkilot"],
        )

        # Salary
        salary_text = self.get_field_value(
            text_clean,
            ["Маош", "Maosh", "Зарплата", "Salary", "Oylik"],
        )
        sal_min, sal_max, sal_currency = self.extract_salary(salary_text)

        # Location
        location = self.get_field_value(
            text_clean,
            ["Манзил", "Manzil", "Адрес", "Location"],
        )

        # Source URL (application forms)
        source_url = ""
        urls = self.extract_urls(text_clean)
        for url in urls:
            if "t.me" not in url:
                source_url = url
                break

        # Contact
        contact = self.get_field_value(
            text_clean,
            ["Murojaat", "Мурожаат", "Обращаться", "Контакт", "Aloqa"],
        )
        if not contact:
            contact = self.extract_contacts(text_clean)
        if not contact and source_url:
            contact = source_url

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
