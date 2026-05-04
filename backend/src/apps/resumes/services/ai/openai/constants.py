"""Constants used across the OpenAI service."""

# Model configuration
DEFAULT_MODEL = "gpt-4o"
FALLBACK_MODEL = "gpt-4-turbo-preview"
FAST_MODEL = "gpt-3.5-turbo"  # Much faster for basic extraction
MAX_TOKENS = 4000
TEMPERATURE = 0.3

# Date format constants
DATE_FORMATS = ("%Y-%m-%d", "%Y-%m", "%B %Y", "%B")
OUTPUT_DATE_FORMAT = "%Y-%m-%d"
DISPLAY_DATE_FORMAT = "%m/%Y"

# Month mapping for date parsing
MONTH_MAP = {
    "jan": "01",
    "january": "01",
    "feb": "02",
    "february": "02",
    "mar": "03",
    "march": "03",
    "apr": "04",
    "april": "04",
    "may": "05",
    "jun": "06",
    "june": "06",
    "jul": "07",
    "july": "07",
    "aug": "08",
    "august": "08",
    "sep": "09",
    "september": "09",
    "oct": "10",
    "october": "10",
    "nov": "11",
    "november": "11",
    "dec": "12",
    "december": "12",
}
