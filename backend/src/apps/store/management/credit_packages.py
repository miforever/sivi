# apps/store/credit_packages.py
"""Credit package configurations."""

RESUME_CREDIT_PACKS = {
    "1": {"credits": 1, "price": 9000, "currency": "UZS"},
    "2": {"credits": 2, "price": 16000, "currency": "UZS"},
    "3": {"credits": 3, "price": 20000, "currency": "UZS"},
}


def get_credit_packs():
    """Get all credit packages configuration."""
    return RESUME_CREDIT_PACKS


def get_credit_pack(pack_id: str):
    """Get a specific credit package by ID."""
    return RESUME_CREDIT_PACKS.get(pack_id)
