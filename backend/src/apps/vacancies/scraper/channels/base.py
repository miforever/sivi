import re
from abc import ABC, abstractmethod

from apps.vacancies.scraper.base import ParsedVacancy as ParsedVacancy
from apps.vacancies.scraper.base import extract_skills_from_text


class BaseChannelParser(ABC):
    """Base class for channel-specific vacancy parsers.

    Subclasses must set `channel_username` and `channel_name`,
    and implement `is_vacancy()` and `extract()`.
    """

    channel_username: str
    channel_name: str

    def parse(self, message: dict) -> ParsedVacancy | None:
        """Template method: filter non-vacancy posts, then extract."""
        if not message.get("text", "").strip():
            return None
        if not self.is_vacancy(message):
            return None
        vacancy = self.extract(message)
        if vacancy and not vacancy.is_valid:
            return None
        return vacancy

    @abstractmethod
    def is_vacancy(self, message: dict) -> bool:
        """Return True if message is a job posting (not an ad, greeting, etc.)."""
        ...

    @abstractmethod
    def extract(self, message: dict) -> ParsedVacancy | None:
        """Extract structured vacancy data from the message."""
        ...

    # ------------------------------------------------------------------
    # Shared utilities — available to all subclasses
    # ------------------------------------------------------------------

    # Common salary patterns across channels
    # Handles: "150к-350к", "от 4000+$", "от 4000$ до 5000$", "5 000 000 UZS"
    _SALARY_PATTERN = re.compile(
        r"(?P<min>\d[\d\s.,]*[кk]?)"
        r"(?:\s*(?:[-–—]|до)\s*(?P<max>\d[\d\s.,]*[кk]?))?"
        r"\+?"
        r"\s*(?P<currency>UZS|USD|RUB|so[ʻ']?m|сўм|сум|руб|₽|\$|usd|uzs|rub)?",
        re.IGNORECASE,
    )

    _EXPERIENCE_PATTERN = re.compile(
        r"(\d+)\+?\s*(?:yil|лет|год|year|years|г\.?)",
        re.IGNORECASE,
    )

    _TELEGRAM_MENTION_PATTERN = re.compile(r"@[\w]+")
    _PHONE_PATTERN = re.compile(r"\+?\d[\d\s()-]{7,}")
    _URL_PATTERN = re.compile(r"https?://\S+")

    def extract_salary(self, text: str) -> tuple[int | None, int | None, str]:
        """Extract salary range and currency from text.

        Returns (min, max, currency). Handles:
        - "5 000 000 - 10 000 000 UZS"
        - "$1600 - 1800"
        - "от 3 000 000 сум"
        - "300$+"
        """
        if not text:
            return None, None, ""

        # Detect currency first
        currency = ""
        if re.search(r"\$|usd", text, re.IGNORECASE):
            currency = "USD"
        elif re.search(r"руб|₽|rub", text, re.IGNORECASE):
            currency = "RUB"
        elif re.search(r"UZS|so[ʻ']?m|сўм|сум|ming|mln|млн", text, re.IGNORECASE):
            currency = "UZS"

        match = self._SALARY_PATTERN.search(text)
        if not match:
            return None, None, currency

        def parse_num(s: str) -> int | None:
            if not s:
                return None
            # Handle "к"/"k" shorthand for thousands (e.g. "150к" = 150000)
            has_k = bool(re.search(r"[кk]$", s.strip(), re.IGNORECASE))
            cleaned = re.sub(r"[\s.,кk]", "", s.strip(), flags=re.IGNORECASE)
            try:
                val = int(cleaned)
                return val * 1000 if has_k else val
            except ValueError:
                return None

        sal_min = parse_num(match.group("min"))
        sal_max = parse_num(match.group("max"))

        if not currency and match.group("currency"):
            raw_cur = match.group("currency").lower()
            if raw_cur in ("$", "usd"):
                currency = "USD"
            elif raw_cur in ("руб", "₽", "rub"):
                currency = "RUB"
            else:
                currency = "UZS"

        # "ming" means thousands in Uzbek (e.g., "600 ming" = 600,000)
        # Only apply if number is small (not already expanded)
        if "ming" in text.lower():
            if sal_min and sal_min < 100_000:
                sal_min *= 1000
            if sal_max and sal_max < 100_000:
                sal_max *= 1000

        # "mln" / "млн" means millions (e.g., "4 mln" = 4,000,000)
        # Only apply if number is small (not already in full form)
        if re.search(r"mln|млн", text, re.IGNORECASE):
            if sal_min and sal_min < 1_000:
                sal_min *= 1_000_000
            if sal_max and sal_max < 1_000:
                sal_max *= 1_000_000

        # Infer currency when not explicitly mentioned:
        # millions → UZS (Uzbek soums), thousands → USD
        if not currency and (sal_min or sal_max):
            ref = sal_min or sal_max
            if ref >= 100_000:
                currency = "UZS"
            else:
                currency = "USD"

        # Safety: clamp to PostgreSQL integer range
        pg_int_max = 2_147_483_647
        if sal_min and sal_min > pg_int_max:
            sal_min = pg_int_max
        if sal_max and sal_max > pg_int_max:
            sal_max = pg_int_max

        return sal_min, sal_max, currency

    def extract_experience(self, text: str) -> int | None:
        """Extract minimum years of experience from text."""
        match = self._EXPERIENCE_PATTERN.search(text)
        if not match:
            return None
        years = int(match.group(1))
        # Sanity: ignore impossible values (e.g. "2024 год" parsed as 2024 years)
        return years if years <= 50 else None

    def extract_skills(self, text: str) -> list[str]:
        """Extract recognized skills from text."""
        return extract_skills_from_text(text)

    def extract_contacts(self, text: str) -> str:
        """Extract contact info (Telegram handles, phones, URLs)."""
        parts = []
        mentions = self._TELEGRAM_MENTION_PATTERN.findall(text)
        phones = self._PHONE_PATTERN.findall(text)
        parts.extend(mentions)
        for p in phones:
            cleaned = p.strip()
            # Skip salary-like numbers (e.g. "8 000 000", "55 000 000")
            digits_only = re.sub(r"[^\d]", "", cleaned)
            if (
                digits_only
                and not cleaned.startswith("+")
                and int(digits_only) % 1000 == 0
                and int(digits_only) >= 100_000
            ):
                continue
            parts.append(cleaned)
        return ", ".join(parts) if parts else ""

    def extract_urls(self, text: str) -> list[str]:
        """Extract all URLs from text."""
        return self._URL_PATTERN.findall(text)

    def clean_footer(self, text: str, markers: list[str]) -> str:
        """Remove channel footer/promotional text after known markers."""
        for marker in markers:
            idx = text.find(marker)
            if idx != -1:
                text = text[:idx]
        return text.strip()

    def get_field_value(self, text: str, labels: list[str]) -> str:
        """Extract field value after a label like 'Компания:' or 'Maosh:'.

        Handles both single-line values and labels that appear at end of
        a dash-prefixed line (e.g., '— Maosh: 5 000 000').
        """
        for label in labels:
            pattern = re.compile(
                rf"(?:^|—\s*){re.escape(label)}\s*:\s*(.+?)$",
                re.MULTILINE,
            )
            match = pattern.search(text)
            if match:
                return match.group(1).strip()
        return ""

    def get_section_content(self, text: str, headers: list[str]) -> str:
        """Extract multi-line section content below a header.

        Captures all lines after the header until the next section or end.
        Handles bullet points (•, -, —).
        """
        for header in headers:
            pattern = re.compile(
                rf"{re.escape(header)}\s*:?\s*\n((?:[\s•\-—].*\n?)*)",
                re.MULTILINE,
            )
            match = pattern.search(text)
            if match:
                return match.group(1).strip()
        return ""

    def detect_work_format(self, text: str) -> str:
        """Detect work format: remote, office, or hybrid."""
        lower = text.lower()
        if any(w in lower for w in ("remote", "masofaviy", "удалённ", "online")):
            return "remote"
        if any(w in lower for w in ("hybrid", "гибрид", "gibrid")):
            return "hybrid"
        if any(w in lower for w in ("office", "oflayn", "offline", "ofis")):
            return "office"
        return ""

    def detect_employment_type(self, text: str) -> str:
        """Detect employment type from text."""
        lower = text.lower()
        if any(w in lower for w in ("internship", "amaliyot", "стажировка", "стажёр")):
            return "internship"
        if any(w in lower for w in ("freelance", "фриланс")):
            return "freelance"
        if any(w in lower for w in ("part-time", "part time", "yarim stavka", "частичн")):
            return "part_time"
        if any(w in lower for w in ("contract", "shartnoma", "контракт", "лойиҳавий")):
            return "contract"
        return "full_time"
