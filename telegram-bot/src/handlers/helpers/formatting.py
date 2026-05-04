import re
from urllib.parse import urlparse


def is_url(string: str) -> bool:
    try:
        result = urlparse(string)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def should_use_map_link(location_str):
    """Determine if location is detailed enough to need a map link"""
    if not location_str:
        return False

    # Replace common separators with spaces, then split
    # Handles: commas, semicolons, pipes, slashes, dashes, etc.
    cleaned = re.sub(r"[,;|/\-\u2014\u2013]+", " ", location_str)
    words = cleaned.split()

    return len(words) >= 4


def google_maps_link(location: str) -> str:
    base_url = "https://www.google.com/maps/search/?api=1&query="
    query = location.replace(" ", "+")
    return f"{base_url}{query}"


def format_number(value) -> str:
    """Format a number with dots as thousand separators.

    Args:
        value: Numeric value to format

    Returns:
        Formatted number string with dot separators, or empty string if falsy
    """
    if not value:
        return ""
    try:
        return f"{int(value):,}".replace(",", ".")
    except (ValueError, TypeError):
        return str(value)
