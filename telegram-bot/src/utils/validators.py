"""Lightweight input validators for user-provided resume fields."""

import re

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_PHONE_ALLOWED_RE = re.compile(r"^[\d\s+()\-./]+$")


def validate_full_name(text: str) -> bool:
    """Full name must contain at least two whitespace-separated tokens
    of at least two characters each."""
    if not text:
        return False
    tokens = [t for t in text.strip().split() if len(t) >= 2]
    return len(tokens) >= 2


def validate_email(text: str) -> bool:
    if not text:
        return False
    return bool(_EMAIL_RE.match(text.strip()))


def validate_phone(text: str) -> bool:
    """Accept international / local phone formats. Requires at least 7 digits
    and only allows digits plus common separators."""
    if not text:
        return False
    stripped = text.strip()
    if not _PHONE_ALLOWED_RE.match(stripped):
        return False
    digits = re.sub(r"\D", "", stripped)
    return 7 <= len(digits) <= 15
