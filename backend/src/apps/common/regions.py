"""Region registry for Uzbekistan.

Loads static_data/regions.json once at import time and exposes helpers for:
- Looking up localised region names
- Resolving a free-text location string to a canonical region slug

Slug → region mapping is the authoritative reference used by the Vacancy
model's `region` field and the User model's `preferred_regions` field.
"""

import json
from functools import lru_cache
from pathlib import Path

_REGIONS_FILE = Path(__file__).resolve().parents[3] / "static_data" / "regions.json"

with _REGIONS_FILE.open(encoding="utf-8") as _f:
    REGIONS: dict[str, dict] = json.load(_f)

REGION_SLUGS: list[str] = list(REGIONS.keys())

# (slug, display_name) pairs — English names for choices
REGION_CHOICES: list[tuple[str, str]] = [(slug, data["name_en"]) for slug, data in REGIONS.items()]


def get_region_name(slug: str, lang: str = "en") -> str:
    """Return the localised region name for a slug.

    lang: "en" | "uz" | "cyr" (Uzbek Cyrillic) | "ru"
    """
    region = REGIONS.get(slug)
    if not region:
        return slug
    key_map = {
        "en": "name_en",
        "uz": "name_uz",
        "cyr": "name_uz_cyr",
        "ru": "name_ru",
    }
    key = key_map.get(lang, "name_en")
    return region.get(key) or region.get("name_en") or slug


# ---------------------------------------------------------------------------
# City / region → slug lookup table
# ---------------------------------------------------------------------------
# Maps every known city/region name variant (in all supported languages and
# common transliterations) to a region slug.  Keys are lowercased.

_CITY_TO_REGION: dict[str, str] = {
    # ── Tashkent city ──────────────────────────────────────────────────────
    "tashkent": "tashkent_city",
    "toshkent": "tashkent_city",
    "toshkent shahri": "tashkent_city",
    "toshkent sh": "tashkent_city",
    "ташкент": "tashkent_city",
    "г. ташкент": "tashkent_city",
    "г.ташкент": "tashkent_city",
    "город ташкент": "tashkent_city",
    # ── Tashkent region ────────────────────────────────────────────────────
    "tashkent region": "tashkent_region",
    "tashkent viloyati": "tashkent_region",
    "toshkent viloyati": "tashkent_region",
    "toshkent oblast": "tashkent_region",
    "ташкентская область": "tashkent_region",
    "ташкентская обл": "tashkent_region",
    # cities inside tashkent region (gorodrabot subdomains)
    "akkurgan": "tashkent_region",
    "almalyik": "tashkent_region",
    "almaliq": "tashkent_region",
    "almалык": "tashkent_region",
    "angren": "tashkent_region",
    "ahangaran": "tashkent_region",
    "bekabad": "tashkent_region",
    "bекабад": "tashkent_region",
    "gazalkent": "tashkent_region",
    "keles": "tashkent_region",
    "nurafshon": "tashkent_region",
    "нурафшон": "tashkent_region",
    "parkent": "tashkent_region",
    "pskent": "tashkent_region",
    "yangiyul": "tashkent_region",
    "янгиюль": "tashkent_region",
    "chinaz": "tashkent_region",
    "chirchik": "tashkent_region",
    "чирчик": "tashkent_region",
    "zangiota": "tashkent_region",
    # ── Andijan ────────────────────────────────────────────────────────────
    "andijan": "andijan",
    "andijon": "andijan",
    "андижан": "andijan",
    "андижанская область": "andijan",
    "andijon viloyati": "andijan",
    # ── Bukhara ────────────────────────────────────────────────────────────
    "bukhara": "bukhara",
    "buxoro": "bukhara",
    "бухара": "bukhara",
    "бухарская область": "bukhara",
    "buxoro viloyati": "bukhara",
    # cities inside bukhara region
    "gijduvan": "bukhara",
    "kagan": "bukhara",
    "каган": "bukhara",
    # ── Jizzakh ────────────────────────────────────────────────────────────
    "jizzakh": "jizzakh",
    "jizzax": "jizzakh",
    "джизак": "jizzakh",
    "жиззах": "jizzakh",
    "джизакская область": "jizzakh",
    "jizzax viloyati": "jizzakh",
    # cities
    "pahtakor": "jizzakh",
    "djuma": "jizzakh",
    "djambay": "jizzakh",
    # ── Kashkadarya ────────────────────────────────────────────────────────
    "kashkadarya": "kashkadarya",
    "qashqadaryo": "kashkadarya",
    "карши": "kashkadarya",
    "кашкадарья": "kashkadarya",
    "кашкадарьинская область": "kashkadarya",
    "qashqadaryo viloyati": "kashkadarya",
    # cities
    "karshi": "kashkadarya",
    "shahrisabz": "kashkadarya",
    "шахрисабз": "kashkadarya",
    "guzar": "kashkadarya",
    "kitab": "kashkadarya",
    # ── Navoi ──────────────────────────────────────────────────────────────
    "navoi": "navoi",
    "navoiy": "navoi",
    "навои": "navoi",
    "навоийская область": "navoi",
    "navoiy viloyati": "navoi",
    # cities
    "zarafshan": "navoi",
    "зарафшан": "navoi",
    "gazli": "navoi",
    "uchkuduk": "navoi",
    # ── Namangan ───────────────────────────────────────────────────────────
    "namangan": "namangan",
    "наманган": "namangan",
    "наманганская область": "namangan",
    "namangan viloyati": "namangan",
    # cities
    "chust": "namangan",
    "чуст": "namangan",
    # ── Samarkand ──────────────────────────────────────────────────────────
    "samarkand": "samarkand",
    "samarqand": "samarkand",
    "самарканд": "samarkand",
    "самаркандская область": "samarkand",
    "samarqand viloyati": "samarkand",
    # cities
    "kattakurgan": "samarkand",
    "каттакурган": "samarkand",
    "urgut": "samarkand",
    # ── Surkhandarya ───────────────────────────────────────────────────────
    "surkhandarya": "surkhandarya",
    "surxondaryo": "surkhandarya",
    "термез": "surkhandarya",
    "сурхандарья": "surkhandarya",
    "сурхандарьинская область": "surkhandarya",
    "surxondaryo viloyati": "surkhandarya",
    # cities
    "termez": "surkhandarya",
    "denau": "surkhandarya",
    # ── Syrdarya ───────────────────────────────────────────────────────────
    "syrdarya": "syrdarya",
    "sirdaryo": "syrdarya",
    "гулистан": "syrdarya",
    "сырдарья": "syrdarya",
    "сырдарьинская область": "syrdarya",
    "sirdaryo viloyati": "syrdarya",
    # cities
    "gulistan": "syrdarya",
    "syirdarya": "syrdarya",
    # ── Fergana ────────────────────────────────────────────────────────────
    "fergana": "fergana",
    "farg'ona": "fergana",
    "fargona": "fergana",
    "фергана": "fergana",
    "ферганская область": "fergana",
    "farg'ona viloyati": "fergana",
    # cities
    "kokand": "fergana",
    "коканд": "fergana",
    "margilan": "fergana",
    "маргилан": "fergana",
    # ── Khorezm ────────────────────────────────────────────────────────────
    "khorezm": "khorezm",
    "xorazm": "khorezm",
    "хорезм": "khorezm",
    "хорезмская область": "khorezm",
    "xorazm viloyati": "khorezm",
    # cities
    "urgench": "khorezm",
    "urganch": "khorezm",
    "ургенч": "khorezm",
    "хива": "khorezm",
    "hiva": "khorezm",
    # ── Karakalpakstan ─────────────────────────────────────────────────────
    "karakalpakstan": "karakalpakstan",
    "qoraqalpog'iston": "karakalpakstan",
    "каракалпакстан": "karakalpakstan",
    "республика каракалпакстан": "karakalpakstan",
    "каракалпакия": "karakalpakstan",
    # cities
    "nukus": "karakalpakstan",
    "нукус": "karakalpakstan",
    "muynak": "karakalpakstan",
}


@lru_cache(maxsize=2048)
def resolve_region(location_text: str) -> str:
    """Map a free-text location string to a region slug.

    Returns empty string for Remote/unknown locations.
    Caches results (common locations repeat thousands of times per scrape run).
    """
    if not location_text:
        return ""

    lower = location_text.lower().strip()

    # Remote/online → no specific region
    if any(w in lower for w in ("remote", "удалённо", "удаленно", "masofaviy", "online")):
        return ""

    # Exact match first
    if lower in _CITY_TO_REGION:
        return _CITY_TO_REGION[lower]

    # Prefix match — "Tashkent, Chilanzar" → "tashkent_city"
    for key, slug in _CITY_TO_REGION.items():
        if lower.startswith(key):
            return slug

    # Substring match — "Улица Бобура, Ташкент" → check if any key is contained
    for key, slug in _CITY_TO_REGION.items():
        if len(key) > 4 and key in lower:
            return slug

    return ""
