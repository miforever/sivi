"""Currency exchange rate utilities for analytics."""

import logging

import httpx
from django.core.cache import cache

logger = logging.getLogger(__name__)

_CACHE_KEY = "usd_uzs_rate"
_CACHE_TTL = 60 * 60 * 24  # 24 hours
_FALLBACK_RATE = 12_800.0  # approximate USD → UZS fallback


def get_usd_to_uzs_rate() -> float:
    """Return the current USD → UZS exchange rate (cached 24h)."""
    rate = cache.get(_CACHE_KEY)
    if rate is not None:
        return float(rate)

    try:
        resp = httpx.get(
            "https://open.er-api.com/v6/latest/USD",
            timeout=10.0,
        )
        resp.raise_for_status()
        data = resp.json()
        rate = float(data["rates"]["UZS"])
        cache.set(_CACHE_KEY, rate, _CACHE_TTL)
        logger.info("Fetched USD→UZS rate: %.2f", rate)
        return rate
    except Exception:
        logger.warning("Failed to fetch exchange rate, using fallback %.0f", _FALLBACK_RATE)
        return _FALLBACK_RATE
