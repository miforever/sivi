"""Celery tasks for vacancy scraping (Telegram channels + job platforms)."""

import logging
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def scrape_channel_task(self, channel_username: str, limit: int = 50):
    """Scrape a single Telegram channel for job vacancies.

    Isolated per channel — one channel failing doesn't block others.
    """
    from apps.vacancies.scraper.service import ScraperService

    service = ScraperService()
    try:
        return service.scrape_channel(channel_username, limit=limit)
    except Exception as exc:
        logger.exception("scrape_channel_task failed for @%s", channel_username)
        raise self.retry(exc=exc)


@shared_task
def scrape_all_channels_task(limit: int = 50):
    """Fan-out: dispatch one scrape_channel_task per configured channel."""
    channels = list(settings.TELEGRAM_JOB_CHANNELS.keys())
    logger.info("Dispatching scrape tasks for %d channels", len(channels))
    for channel_username in channels:
        scrape_channel_task.delay(channel_username, limit=limit)


# ---------------------------------------------------------------------------
# Platform tasks
# ---------------------------------------------------------------------------


@shared_task(bind=True, max_retries=3, default_retry_delay=120)
def scrape_platform_task(self, platform_name: str, max_pages: int = 1000):
    """Scrape a single job platform (e.g. hh_uz) for vacancies."""
    from apps.vacancies.scraper.platforms.service import PlatformScraperService

    service = PlatformScraperService()
    try:
        return service.scrape_platform(platform_name, max_pages=max_pages)
    except Exception as exc:
        logger.exception("scrape_platform_task failed for %s", platform_name)
        raise self.retry(exc=exc)


@shared_task
def scrape_all_platforms_task(max_pages: int = 1000):
    """Fan-out: dispatch one scrape_platform_task per registered platform."""
    from apps.vacancies.scraper.platforms import PLATFORM_REGISTRY

    platforms = list(PLATFORM_REGISTRY.keys())
    logger.info("Dispatching scrape tasks for %d platforms", len(platforms))
    for platform_name in platforms:
        scrape_platform_task.delay(platform_name, max_pages=max_pages)


# ---------------------------------------------------------------------------
# Cleanup tasks
# ---------------------------------------------------------------------------

VACANCY_RETENTION_DAYS = 60


@shared_task
def purge_stale_vacancies_task():
    """Delete vacancies older than 60 days to keep the dataset fresh."""
    from apps.vacancies.models import Vacancy

    cutoff = timezone.now() - timedelta(days=VACANCY_RETENTION_DAYS)
    count, _ = Vacancy.objects.filter(created_at__lt=cutoff).delete()
    logger.info("Purged %d stale vacancies (older than %s)", count, cutoff.date())
    return {"deleted": count}
