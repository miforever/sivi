"""Date processing functionality for resume data."""

import logging
from datetime import datetime
from typing import Any

from dateutil.relativedelta import relativedelta

logger = logging.getLogger(__name__)


class DateProcessor:
    """Handles date processing and duration calculations for resume items."""

    @staticmethod
    def normalize_date_to_standard(date_str: str, is_start_date: bool = True) -> str | None:
        """
        Normalize various date formats to YYYY-MM-DD format.

        Args:
            date_str: Date string in various formats.
            is_start_date: Whether this is a start date (affects day selection).

        Returns:
            Normalized date string in YYYY-MM-DD format or None if parsing fails.
        """
        if not date_str or not isinstance(date_str, str):
            return None

        date_str = date_str.strip()

        # Handle "Present", "Current", "Now" - should return None for end_date
        if date_str.lower() in ["present", "current", "now", "ongoing", "null", "none", ""]:
            return None

        try:
            # Try to parse if already in YYYY-MM-DD format
            if len(date_str) == 10 and date_str.count("-") == 2:
                datetime.strptime(date_str, "%Y-%m-%d")
                return date_str

            # Handle YYYY-MM format
            if len(date_str) == 7 and date_str.count("-") == 1:
                year, month = date_str.split("-")
                if year.isdigit() and month.isdigit() and 1 <= int(month) <= 12:
                    day = "01" if is_start_date else "28"  # Use 28 to avoid month-end issues
                    return f"{year}-{month.zfill(2)}-{day}"

            # Handle year only (YYYY)
            if len(date_str) == 4 and date_str.isdigit():
                year = int(date_str)
                if 1900 <= year <= 2100:  # Reasonable year range
                    month = "01" if is_start_date else "12"
                    day = "01" if is_start_date else "31"
                    return f"{date_str}-{month}-{day}"

            # Handle MM/YYYY format
            if "/" in date_str and len(date_str.split("/")) == 2:
                parts = date_str.split("/")
                if len(parts[0]) <= 2 and len(parts[1]) == 4:  # MM/YYYY
                    month, year = parts
                    if (
                        month.isdigit()
                        and year.isdigit()
                        and 1 <= int(month) <= 12
                        and 1900 <= int(year) <= 2100
                    ):
                        month = month.zfill(2)
                        day = "01" if is_start_date else "28"
                        return f"{year}-{month}-{day}"

            # Handle YYYY/MM format
            if "/" in date_str and len(date_str.split("/")) == 2:
                parts = date_str.split("/")
                if len(parts[0]) == 4 and len(parts[1]) <= 2:  # YYYY/MM
                    year, month = parts
                    if (
                        year.isdigit()
                        and month.isdigit()
                        and 1900 <= int(year) <= 2100
                        and 1 <= int(month) <= 12
                    ):
                        month = month.zfill(2)
                        day = "01" if is_start_date else "28"
                        return f"{year}-{month}-{day}"

            # Handle other common formats
            common_formats = [
                "%Y-%m-%d",
                "%Y/%m/%d",
                "%m/%d/%Y",
                "%d/%m/%Y",
                "%Y-%m",
                "%m/%Y",
                "%B %Y",
                "%b %Y",
                "%Y",
            ]

            for fmt in common_formats:
                try:
                    parsed_date = datetime.strptime(date_str, fmt)
                    # For formats without day, set to 1st or last day of month
                    if "%d" not in fmt:
                        if is_start_date:
                            parsed_date = parsed_date.replace(day=1)
                        else:
                            # Get last day of month
                            next_month = parsed_date.replace(day=28) + relativedelta(days=4)
                            parsed_date = next_month - relativedelta(days=next_month.day)
                    return parsed_date.strftime("%Y-%m-%d")
                except ValueError:
                    continue

        except Exception as e:
            logger.warning(f"Failed to normalize date '{date_str}': {e}")

        # If all else fails, try to extract year and month from the string
        try:
            # Look for 4-digit year
            import re

            year_match = re.search(r"\b(19|20)\d{2}\b", date_str)
            if year_match:
                year = year_match.group(0)
                # Look for month (1-12 or month names)
                month_match = re.search(r"\b(0?[1-9]|1[0-2])\b", date_str)
                if month_match:
                    month = month_match.group(0).zfill(2)
                    day = "01" if is_start_date else "28"
                    return f"{year}-{month}-{day}"
                else:
                    # Only year found, use default month
                    month = "01" if is_start_date else "12"
                    day = "01" if is_start_date else "31"
                    return f"{year}-{month}-{day}"
        except Exception as e:
            logger.warning(f"Failed to extract date components from '{date_str}': {e}")

        return None

    @staticmethod
    def calculate_duration_between_dates(start_date: str | None, end_date: str | None) -> str:
        """
        Calculate duration between two dates in YYYY-MM-DD format.

        Args:
            start_date: Start date in YYYY-MM-DD format.
            end_date: End date in YYYY-MM-DD format or None for current date.

        Returns:
            Formatted duration string (e.g., "2 years 3 months").
        """
        if not start_date:
            return ""

        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")

            # Use current date if end_date is None (for current positions)
            if end_date is None:
                end = datetime.now()
            else:
                end = datetime.strptime(end_date, "%Y-%m-%d")

            # Calculate difference using relativedelta for accurate month calculation
            delta = relativedelta(end, start)

            # Handle negative duration (shouldn't happen but just in case)
            if delta.years < 0 or (delta.years == 0 and delta.months < 0):
                return ""

            # Format the duration
            years = delta.years
            months = delta.months

            duration_parts = []
            if years > 0:
                duration_parts.append(f"{years} {'year' if years == 1 else 'years'}")
            if months > 0:
                duration_parts.append(f"{months} {'month' if months == 1 else 'months'}")

            return " ".join(duration_parts) if duration_parts else "Less than a month"

        except (ValueError, TypeError) as e:
            logger.warning(
                f"Error calculating duration between '{start_date}' and '{end_date}': {e}"
            )
            return ""

    @staticmethod
    def is_current_position(end_date: str | None) -> bool:
        """
        Determine if a position is current based on end_date.

        Args:
            end_date: End date string or None.

        Returns:
            True if position is current, False otherwise.
        """
        return end_date is None

    @staticmethod
    def process_dates_and_duration(item: dict[str, Any]) -> None:
        """
        Process dates and calculate duration for experiences/education/projects/volunteer work.

        Args:
            item: Dictionary containing date information to process.
        """
        # Get original dates
        original_start = item.get("start_date", "")
        original_end = item.get("end_date", "")

        # Normalize start date - this is REQUIRED, so we need to ensure it's valid
        normalized_start = DateProcessor.normalize_date_to_standard(
            str(original_start) if original_start else "", is_start_date=True
        )

        # If start_date is still invalid, try to infer from context or use a reasonable default
        if not normalized_start:
            # Try to extract year from the original string
            if original_start and isinstance(original_start, str):
                import re

                year_match = re.search(r"\b(19|20)\d{2}\b", original_start)
                if year_match:
                    year = year_match.group(0)
                    normalized_start = f"{year}-01-01"  # Default to January 1st
                else:
                    # Use current year as fallback
                    current_year = datetime.now().year
                    normalized_start = f"{current_year}-01-01"
            else:
                # Use current year as fallback
                current_year = datetime.now().year
                normalized_start = f"{current_year}-01-01"

        item["start_date"] = normalized_start

        # Normalize end date - handle current positions
        if original_end and str(original_end).lower() not in [
            "present",
            "current",
            "now",
            "ongoing",
            "null",
            "none",
            "",
        ]:
            normalized_end = DateProcessor.normalize_date_to_standard(
                str(original_end), is_start_date=False
            )
            item["end_date"] = normalized_end
        else:
            # Current position
            item["end_date"] = None

        # Set current flag based on end_date
        item["current"] = DateProcessor.is_current_position(item["end_date"])

        # Calculate duration
        item["duration"] = DateProcessor.calculate_duration_between_dates(
            item["start_date"], item["end_date"]
        )

        # Log for debugging
        logger.debug(
            f"Processed dates: start='{item['start_date']}', end='{item['end_date']}', "
            f"current={item['current']}, duration='{item['duration']}'"
        )

    @staticmethod
    def validate_date_consistency(resume_data: dict[str, Any]) -> dict[str, Any]:
        """
        Validate date consistency across all resume sections.

        Args:
            resume_data: Complete resume data.

        Returns:
            Validation report with issues found.
        """
        issues = []
        warnings = []

        def check_date_format(date_str: str, field_name: str, item_type: str, item_name: str):
            """Check if date is in correct format."""
            if not date_str:
                return

            try:
                datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                issues.append(
                    f"{item_type} '{item_name}' has invalid {field_name} format: '{date_str}'"
                )

        def check_date_logic(
            start_date: str, end_date: str | None, current: bool, item_type: str, item_name: str
        ):
            """Check date logic consistency."""
            if start_date and end_date:
                try:
                    start = datetime.strptime(start_date, "%Y-%m-%d")
                    end = datetime.strptime(end_date, "%Y-%m-%d")
                    if start > end:
                        issues.append(f"{item_type} '{item_name}' has start date after end date")
                except ValueError:
                    pass  # Format issues already caught above

            # Check current flag consistency
            if current and end_date is not None:
                warnings.append(f"{item_type} '{item_name}' marked as current but has end date")
            elif not current and end_date is None:
                warnings.append(
                    f"{item_type} '{item_name}' not marked as current but has no end date"
                )

        # Check experiences
        for exp in resume_data.get("experiences", []):
            item_name = f"{exp.get('position', 'Unknown')} at {exp.get('company', 'Unknown')}"
            check_date_format(exp.get("start_date", ""), "start_date", "Experience", item_name)
            if exp.get("end_date"):
                check_date_format(exp.get("end_date"), "end_date", "Experience", item_name)
            check_date_logic(
                exp.get("start_date", ""),
                exp.get("end_date"),
                exp.get("current", False),
                "Experience",
                item_name,
            )

        # Check education
        for edu in resume_data.get("education", []):
            item_name = f"{edu.get('degree', 'Unknown')} at {edu.get('institution', 'Unknown')}"
            check_date_format(edu.get("start_date", ""), "start_date", "Education", item_name)
            if edu.get("end_date"):
                check_date_format(edu.get("end_date"), "end_date", "Education", item_name)
            check_date_logic(
                edu.get("start_date", ""),
                edu.get("end_date"),
                edu.get("current", False),
                "Education",
                item_name,
            )

        # Check projects
        for proj in resume_data.get("projects", []):
            item_name = proj.get("name", "Unknown Project")
            check_date_format(proj.get("start_date", ""), "start_date", "Project", item_name)
            if proj.get("end_date"):
                check_date_format(proj.get("end_date"), "end_date", "Project", item_name)
            check_date_logic(
                proj.get("start_date", ""),
                proj.get("end_date"),
                proj.get("current", False),
                "Project",
                item_name,
            )

        # Check volunteer experience
        for vol in resume_data.get("volunteer_experience", []):
            item_name = f"{vol.get('position', 'Unknown')} at {vol.get('organization', 'Unknown')}"
            check_date_format(vol.get("start_date", ""), "start_date", "Volunteer", item_name)
            if vol.get("end_date"):
                check_date_format(vol.get("end_date"), "end_date", "Volunteer", item_name)
            check_date_logic(
                vol.get("start_date", ""),
                vol.get("end_date"),
                vol.get("current", False),
                "Volunteer",
                item_name,
            )

        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "total_issues": len(issues),
            "total_warnings": len(warnings),
        }
