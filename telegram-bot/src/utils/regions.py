"""Region data for the Telegram bot.

Mirrors backend/static_data/regions.json but kept as a static list to avoid
any Django/backend dependency in the bot process.
"""

# Ordered list of all 14 regions with localized names.
REGIONS: list[dict] = [
    {
        "slug": "tashkent_city",
        "name_en": "Tashkent",
        "name_ru": "Ташкент",
        "name_uz": "Toshkent shahri",
        "name_cyr": "Тошкент шаҳри",
    },
    {
        "slug": "tashkent_region",
        "name_en": "Tashkent Region",
        "name_ru": "Ташкентская область",
        "name_uz": "Toshkent viloyati",
        "name_cyr": "Тошкент вилояти",
    },
    {
        "slug": "andijan",
        "name_en": "Andijan",
        "name_ru": "Андижан",
        "name_uz": "Andijon",
        "name_cyr": "Андижон",
    },
    {
        "slug": "bukhara",
        "name_en": "Bukhara",
        "name_ru": "Бухара",
        "name_uz": "Buxoro",
        "name_cyr": "Бухоро",
    },
    {
        "slug": "jizzakh",
        "name_en": "Jizzakh",
        "name_ru": "Джизак",
        "name_uz": "Jizzax",
        "name_cyr": "Жиззах",
    },
    {
        "slug": "kashkadarya",
        "name_en": "Kashkadarya",
        "name_ru": "Кашкадарья",
        "name_uz": "Qashqadaryo",
        "name_cyr": "Қашқадарё",
    },
    {
        "slug": "navoi",
        "name_en": "Navoi",
        "name_ru": "Навои",
        "name_uz": "Navoiy",
        "name_cyr": "Навоий",
    },
    {
        "slug": "namangan",
        "name_en": "Namangan",
        "name_ru": "Наманган",
        "name_uz": "Namangan",
        "name_cyr": "Наманган",
    },
    {
        "slug": "samarkand",
        "name_en": "Samarkand",
        "name_ru": "Самарканд",
        "name_uz": "Samarqand",
        "name_cyr": "Самарқанд",
    },
    {
        "slug": "surkhandarya",
        "name_en": "Surkhandarya",
        "name_ru": "Сурхандарья",
        "name_uz": "Surxondaryo",
        "name_cyr": "Сурхондарё",
    },
    {
        "slug": "syrdarya",
        "name_en": "Syrdarya",
        "name_ru": "Сырдарья",
        "name_uz": "Sirdaryo",
        "name_cyr": "Сирдарё",
    },
    {
        "slug": "fergana",
        "name_en": "Fergana",
        "name_ru": "Фергана",
        "name_uz": "Farg'ona",
        "name_cyr": "Фарғона",
    },
    {
        "slug": "khorezm",
        "name_en": "Khorezm",
        "name_ru": "Хорезм",
        "name_uz": "Xorazm",
        "name_cyr": "Хоразм",
    },
    {
        "slug": "karakalpakstan",
        "name_en": "Karakalpakstan",
        "name_ru": "Каракалпакстан",
        "name_uz": "Qoraqalpog'iston",
        "name_cyr": "Қорақалпоғистон",
    },
]

REGION_SLUGS: list[str] = [r["slug"] for r in REGIONS]

_LANG_KEY_MAP = {
    "uz": "name_uz",
    "cyr": "name_cyr",
    "ru": "name_ru",
    "en": "name_en",
}


def get_region_label(slug: str, lang: str = "en") -> str:
    """Return the localized name for a region slug."""
    key = _LANG_KEY_MAP.get(lang, "name_en")
    for region in REGIONS:
        if region["slug"] == slug:
            return region.get(key) or region["name_en"]
    return slug
