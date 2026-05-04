"""Normalize parsed vacancy data into a clean, uniform format.

Every vacancy goes through this before storage, regardless of source channel.
Handles: emoji removal, whitespace cleanup, footer stripping, field standardization.
"""

import re

from apps.common.regions import resolve_region
from apps.vacancies.scraper.base import ParsedVacancy

# ---------------------------------------------------------------------------
# Emoji / special character removal
# ---------------------------------------------------------------------------

# Matches most emoji, symbols, pictographs, dingbats, variation selectors, ZWJ
_EMOJI_PATTERN = re.compile(
    "["
    "\U0001f600-\U0001f64f"  # emoticons
    "\U0001f300-\U0001f5ff"  # misc symbols & pictographs
    "\U0001f680-\U0001f6ff"  # transport & map
    "\U0001f1e0-\U0001f1ff"  # flags
    "\U0001f900-\U0001f9ff"  # supplemental symbols
    "\U0001fa00-\U0001fa6f"  # chess symbols
    "\U0001fa70-\U0001faff"  # symbols extended-A
    "\U00002702-\U000027b0"  # dingbats
    "\U000024c2-\U0001f251"  # enclosed characters
    "\U0000fe0f"  # variation selector
    "\U0000200d"  # zero width joiner
    "\U00002640-\U00002642"  # gender symbols
    "\U0000200b-\U0000200f"  # zero-width spaces
    "\U00002060"  # word joiner
    "\U0000feff"  # BOM
    "\U00002b50"  # star
    "\U0000274c"  # cross mark
    "\U00002705"  # check mark
    "\U00002714"  # heavy check
    "\U00002716"  # heavy multiplication
    "\U0000203c"  # double exclamation
    "\U00002049"  # exclamation question
    "\U00002139"  # information
    "\U00002934-\U00002935"  # arrows
    "\U000025aa-\U000025ab"  # squares
    "\U000025fb-\U000025fe"  # squares
    "\U00002b05-\U00002b07"  # arrows
    "\U00002b1b-\U00002b1c"  # squares
    "\U00002b55"  # heavy circle
    "\U00003030"  # wavy dash
    "\U000023cf"  # eject
    "\U000023e9-\U000023f3"  # media controls
    "\U000023f8-\U000023fa"  # media controls
    "\U0000231a-\U0000231b"  # watch/hourglass
    "]+",
    flags=re.UNICODE,
)

# Common channel footers and promotional text
_FOOTER_PATTERNS = [
    re.compile(r"👉.*$", re.MULTILINE | re.DOTALL),
    re.compile(r"⭐.*$", re.MULTILINE | re.DOTALL),
    re.compile(r"➖.*$", re.MULTILINE | re.DOTALL),
    re.compile(r"Подписаться на канал.*$", re.MULTILINE | re.DOTALL),
    re.compile(r"Kanalda e.lon joylash.*$", re.MULTILINE | re.DOTALL),
    re.compile(r"Har kunlik e.lonlar.*$", re.MULTILINE | re.DOTALL),
    re.compile(r"Subscribe for daily.*$", re.MULTILINE | re.DOTALL),
    re.compile(r"vakansiya joylash uchun.*$", re.MULTILINE | re.DOTALL | re.IGNORECASE),
]

# Collapse multiple whitespace/newlines
_MULTI_NEWLINE = re.compile(r"\n{3,}")
_MULTI_SPACE = re.compile(r"[ \t]{2,}")
_LEADING_BULLET = re.compile(r"^[\s]*[•\-—–]\s*", re.MULTILINE)

# Location aliases → canonical names
_LOCATION_ALIASES = {
    "toshkent": "Tashkent",
    "toshkent sh": "Tashkent",
    "toshkent shahri": "Tashkent",
    "ташкент": "Tashkent",
    "г. ташкент": "Tashkent",
    "tashkent": "Tashkent",
    "samarqand": "Samarkand",
    "самарканд": "Samarkand",
    "buxoro": "Bukhara",
    "бухара": "Bukhara",
    "farg'ona": "Fergana",
    "fargona": "Fergana",
    "andijon": "Andijan",
    "namangan": "Namangan",
    "navoiy": "Navoi",
    "nukus": "Nukus",
    "xorazm": "Khorezm",
    "urganch": "Urgench",
    "remote": "Remote",
    "удалённо": "Remote",
    "удаленно": "Remote",
    "masofaviy": "Remote",
}

# Employment type normalization
_EMPLOYMENT_ALIASES = {
    "full_time": "full_time",
    "full time": "full_time",
    "полная занятость": "full_time",
    "to'liq stavka": "full_time",
    "part_time": "part_time",
    "part time": "part_time",
    "частичная занятость": "part_time",
    "yarim stavka": "part_time",
    "contract": "contract",
    "контракт": "contract",
    "shartnoma": "contract",
    "лойиҳавий": "contract",
    "internship": "internship",
    "стажировка": "internship",
    "amaliyot": "internship",
    "freelance": "freelance",
    "фриланс": "freelance",
}

# Work format normalization
_WORK_FORMAT_ALIASES = {
    "office": "office",
    "oflayn": "office",
    "offline": "office",
    "офис": "office",
    "на месте работодателя": "office",
    "remote": "remote",
    "online": "remote",
    "удалённо": "remote",
    "удаленно": "remote",
    "масофавий": "remote",
    "hybrid": "hybrid",
    "гибрид": "hybrid",
    "gibrid": "hybrid",
}

# Currency normalization
_CURRENCY_ALIASES = {
    "usd": "USD",
    "$": "USD",
    "доллар": "USD",
    "uzs": "UZS",
    "сум": "UZS",
    "сўм": "UZS",
    "so'm": "UZS",
    "soʻm": "UZS",
    "som": "UZS",
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def normalize(vacancy: ParsedVacancy) -> ParsedVacancy:
    """Normalize a parsed vacancy into a clean, uniform format."""
    normalized_location = _normalize_location(vacancy.location)
    # Use pre-set region (from scraper context) or resolve from location text
    region = (
        vacancy.region or resolve_region(normalized_location) or resolve_region(vacancy.location)
    )

    return ParsedVacancy(
        title=_clean_title(vacancy.title),
        description=_clean_description(vacancy.description),
        company=_clean_text(vacancy.company),
        salary_min=vacancy.salary_min,
        salary_max=vacancy.salary_max,
        salary_currency=_normalize_currency(vacancy.salary_currency),
        employment_type=_normalize_employment_type(vacancy.employment_type),
        work_format=_normalize_work_format(vacancy.work_format),
        location=normalized_location,
        experience_years=vacancy.experience_years,
        skills=_normalize_skills(vacancy.skills),
        contact_info=_clean_text(vacancy.contact_info),
        language=vacancy.language.strip().lower(),
        posted_at=vacancy.posted_at,
        source_url=vacancy.source_url.strip(),
        region=region,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _strip_emojis(text: str) -> str:
    """Remove all emoji and special Unicode symbols."""
    return _EMOJI_PATTERN.sub("", text)


def _clean_whitespace(text: str) -> str:
    """Normalize whitespace: collapse multiple spaces/newlines, strip lines."""
    text = _MULTI_SPACE.sub(" ", text)
    text = _MULTI_NEWLINE.sub("\n\n", text)
    lines = [line.strip() for line in text.split("\n")]
    return "\n".join(lines).strip()


def _strip_footers(text: str) -> str:
    """Remove channel footer / promotional text."""
    for pattern in _FOOTER_PATTERNS:
        text = pattern.sub("", text)
    return text.strip()


def _clean_text(text: str) -> str:
    """General text cleanup: emojis, whitespace, strip."""
    if not text:
        return ""
    text = _strip_emojis(text)
    text = _clean_whitespace(text)
    return text


def _clean_title(title: str) -> str:
    """Clean and normalize a vacancy title."""
    if not title:
        return ""
    title = _strip_emojis(title)
    # Remove common suffixes like "kerak!", "нужен", etc.
    title = re.sub(r"\s*kerak\s*!?\s*$", "", title, flags=re.IGNORECASE)
    title = _clean_whitespace(title)
    # Capitalize first letter
    if title:
        title = title[0].upper() + title[1:]
    return title


def _clean_description(description: str) -> str:
    """Clean vacancy description: strip footers, emojis, normalize formatting."""
    if not description:
        return ""
    description = _strip_footers(description)
    description = _strip_emojis(description)
    # Normalize bullet points to consistent format
    description = _LEADING_BULLET.sub("- ", description)
    description = _clean_whitespace(description)
    return description


def _normalize_location(location: str) -> str:
    """Normalize location to canonical city/region name."""
    if not location:
        return ""
    location = _strip_emojis(location).strip()
    # Check aliases (case-insensitive)
    lower = location.lower().strip()
    for alias, canonical in _LOCATION_ALIASES.items():
        if lower == alias or lower.startswith(alias):
            # Preserve any suffix (e.g., district info) after the city name
            suffix = location[len(alias) :].strip().strip(",").strip()
            if suffix:
                return f"{canonical}, {_clean_text(suffix)}"
            return canonical
    return _clean_text(location)


def _normalize_employment_type(emp_type: str) -> str:
    """Normalize employment type to model choices."""
    if not emp_type:
        return ""
    lower = emp_type.lower().strip()
    return _EMPLOYMENT_ALIASES.get(lower, emp_type)


def _normalize_work_format(work_format: str) -> str:
    """Normalize work format to model choices."""
    if not work_format:
        return ""
    lower = work_format.lower().strip()
    return _WORK_FORMAT_ALIASES.get(lower, work_format)


def _normalize_currency(currency: str) -> str:
    """Normalize currency to uppercase standard code."""
    if not currency:
        return ""
    lower = currency.lower().strip()
    return _CURRENCY_ALIASES.get(lower, currency.upper())


def _normalize_skills(skills: list[str]) -> list[str]:
    """Deduplicate and sort skills."""
    if not skills:
        return []
    seen = set()
    result = []
    for skill in skills:
        key = skill.lower()
        if key not in seen:
            seen.add(key)
            result.append(skill)
    return sorted(result)
