"""Utility functions for date parsing and duration calculations."""

import logging
import re
from datetime import datetime

from dateutil.relativedelta import relativedelta

from .constants import MONTH_MAP

logger = logging.getLogger(__name__)


def parse_date(date_str: str, current_year: int | None = None) -> str:
    """
    Parse a date string into a standardized format (MM/YYYY).

    Args:
        date_str: Date string to parse (can be in various formats).
        current_year: Optional current year for relative dates.

    Returns:
        Formatted date string (MM/YYYY) or original string if parsing fails.
    """
    if not date_str or not isinstance(date_str, str):
        return date_str or ""

    date_str = date_str.strip()

    # Handle "Present" or "Current"
    if date_str.lower() in ["present", "current", "now"]:
        return datetime.now().strftime("%m/%Y")

    # Handle month/year formats
    month_year_pattern = (
        r"(?P<month>Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
        r"Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
        r"[\s\-/,]*(?P<year>\d{2,4})?"
    )
    match = re.search(month_year_pattern, date_str, re.IGNORECASE)

    if match:
        month_str = match.group("month").lower()
        year_str = match.group("year")

        # Convert month to number
        month = MONTH_MAP.get(month_str[:3].lower(), "01")

        # Handle year
        if year_str:
            year = f"20{year_str}" if len(year_str) == 2 and int(year_str) < 50 else year_str
            if len(year_str) == 2 and int(year_str) >= 50:
                year = f"19{year_str}"
        else:
            year = str(current_year or datetime.now().year)

        return f"{month}/{year}"

    # Handle year-only format
    year_match = re.search(r"\b(\d{4})\b", date_str)
    if year_match:
        return f"01/{year_match.group(1)}"

    # If we can't parse it, return the original string
    return date_str


def calculate_duration(start_date: str, end_date: str | None = None) -> str:
    """
    Calculate the duration between two dates in years and months.

    Args:
        start_date: Start date string (MM/YYYY).
        end_date: End date string (MM/YYYY) or None for current date.

    Returns:
        Formatted duration string (e.g., "2 years 3 months").
    """
    if not start_date:
        return ""

    try:
        # Parse start date
        start_parts = start_date.split("/")
        if len(start_parts) != 2:
            return ""

        start_month, start_year = map(int, start_parts)
        start = datetime(start_year, start_month, 1)

        # Parse end date or use current date
        if end_date and end_date.lower() in ["present", "current", "now"]:
            end = datetime.now()
        elif end_date:
            end_parts = end_date.split("/")
            if len(end_parts) != 2:
                end = datetime.now()
            else:
                end_month, end_year = map(int, end_parts)
                end = datetime(end_year, end_month, 1)
        else:
            end = datetime.now()

        # Calculate difference
        delta = relativedelta(end, start)

        # Format the duration
        years = delta.years
        months = delta.months

        duration_parts = []
        if years > 0:
            duration_parts.append(f"{years} {'year' if years == 1 else 'years'}")
        if months > 0:
            duration_parts.append(f"{months} {'month' if months == 1 else 'months'}")

        return " ".join(duration_parts) if duration_parts else "Less than a month"

    except (ValueError, TypeError, AttributeError) as e:
        logger.warning(f"Error calculating duration: {e}")
        return ""


def normalize_date(date_str: str, is_start_date: bool = True) -> str | None:
    """
    Normalize date string to YYYY-MM-DD format.

    Args:
        date_str: Date string to normalize.
        is_start_date: Whether this is a start date (affects day selection).

    Returns:
        Normalized date string or None if parsing fails.
    """
    if not isinstance(date_str, str) or not date_str.strip():
        return None

    date_str = date_str.strip()

    # Handle current position indicators
    if date_str.lower() in ["present", "current", "now", "ongoing"]:
        return None

    try:
        # Handle different date formats
        if len(date_str) == 4 and date_str.isdigit():  # Only year provided (YYYY)
            month = "01" if is_start_date else "12"
            day = "01" if is_start_date else "31"
            return f"{date_str}-{month}-{day}"
        elif len(date_str) == 7 and date_str.count("-") == 1:  # YYYY-MM format
            day = "01" if is_start_date else "28"  # Use 28 to avoid month-end issues
            return f"{date_str}-{day}"
        elif len(date_str) == 10 and date_str.count("-") == 2:  # YYYY-MM-DD format
            # Validate the format
            datetime.strptime(date_str, "%Y-%m-%d")
            return date_str
        elif "/" in date_str:  # Handle MM/YYYY or DD/MM/YYYY formats
            parts = date_str.split("/")
            if len(parts) == 2 and len(parts[1]) == 4:  # MM/YYYY
                month, year = parts
                month = month.zfill(2)
                day = "01" if is_start_date else "28"
                return f"{year}-{month}-{day}"
            elif len(parts) == 3:  # DD/MM/YYYY or MM/DD/YYYY
                # Try to determine format based on values
                if int(parts[0]) > 12:  # DD/MM/YYYY
                    day, month, year = parts
                else:  # MM/DD/YYYY
                    month, day, year = parts
                month = month.zfill(2)
                day = day.zfill(2)
                return f"{year}-{month}-{day}"
        else:
            # Try common date formats
            common_formats = [
                "%Y-%m-%d",
                "%Y/%m/%d",
                "%m/%d/%Y",
                "%d/%m/%Y",
                "%B %d, %Y",
                "%b %d, %Y",
                "%d %B %Y",
                "%d %b %Y",
                "%B %Y",
                "%b %Y",
            ]

            for fmt in common_formats:
                try:
                    parsed_date = datetime.strptime(date_str, fmt)
                    return parsed_date.strftime("%Y-%m-%d")
                except ValueError:
                    continue

    except (ValueError, AttributeError) as e:
        logger.warning(f"Failed to normalize date '{date_str}': {e}")

    return None


def calculate_duration_between_dates(start_date: str | None, end_date: str | None) -> str:
    """
    Calculate duration between two dates in YYYY-MM-DD format.

    Args:
        start_date: Start date in YYYY-MM-DD format.
        end_date: End date in YYYY-MM-DD format or None for current date.

    Returns:
        Formatted duration string.
    """
    if not start_date:
        return ""

    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d") if end_date else datetime.now()

        # Calculate years and months using relativedelta for accuracy
        delta = relativedelta(end, start)

        # Handle negative duration (shouldn't happen but just in case)
        if delta.years < 0 or (delta.years == 0 and delta.months < 0):
            return ""

        # Format duration string
        years = delta.years
        months = delta.months

        duration_parts = []
        if years > 0:
            duration_parts.append(f"{years} {'year' if years == 1 else 'years'}")
        if months > 0:
            duration_parts.append(f"{months} {'month' if months == 1 else 'months'}")

        return " ".join(duration_parts) if duration_parts else "Less than a month"

    except (ValueError, TypeError) as e:
        logger.warning(f"Failed to calculate duration: {e}")
        return ""


def format_date_for_display(date_str: str | None) -> str:
    """
    Format a YYYY-MM-DD date for display purposes.

    Args:
        date_str: Date string in YYYY-MM-DD format or None.

    Returns:
        Formatted date string for display or "Present" if None.
    """
    if not date_str:
        return "Present"

    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj.strftime("%B %Y")  # e.g., "January 2023"
    except (ValueError, TypeError):
        return date_str  # Return original if parsing fails


def validate_date_range(start_date: str | None, end_date: str | None) -> bool:
    """
    Validate that start_date is before end_date.

    Args:
        start_date: Start date in YYYY-MM-DD format.
        end_date: End date in YYYY-MM-DD format or None.

    Returns:
        True if date range is valid, False otherwise.
    """
    if not start_date:
        return False

    if not end_date:  # Current position
        return True

    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        return start <= end
    except (ValueError, TypeError):
        return False
