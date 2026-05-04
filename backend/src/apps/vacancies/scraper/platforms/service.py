"""Scraper service for job platforms (REST APIs)."""

import logging
import time
from datetime import UTC, datetime, timedelta

from django.db import IntegrityError

from apps.vacancies.models import Vacancy, VacancySource
from apps.vacancies.scraper.base import ParsedVacancy
from apps.vacancies.scraper.normalizer import normalize
from apps.vacancies.scraper.platforms import get_platform_parser

MAX_VACANCY_AGE_DAYS = 60

logger = logging.getLogger(__name__)


class PlatformScraperService:
    """Orchestrates the scraping pipeline for a single job platform.

    Supports two modes:
    1. Single-region parsers (no ``scrape_regions`` attribute) — standard
       page loop until empty page.
    2. Multi-region parsers (``scrape_regions: dict[city_key, region_slug]``) —
       iterates each city independently until each city returns an empty page.
    """

    def scrape_platform(
        self,
        platform_name: str,
        max_pages: int = 1000,
        **kwargs,
    ) -> dict:
        """Fetch, normalize, and store vacancies from a platform."""
        results = {
            "platform": platform_name,
            "fetched": 0,
            "created": 0,
            "skipped_duplicate": 0,
            "skipped_invalid": 0,
            "errors": 0,
        }

        parser = get_platform_parser(platform_name)
        scrape_regions: dict | None = getattr(parser, "scrape_regions", None)

        if scrape_regions:
            for i, (city_key, region_slug) in enumerate(scrape_regions.items()):
                if i > 0:
                    time.sleep(0.75)
                self._scrape_pages(
                    parser,
                    platform_name,
                    max_pages,
                    results,
                    region_slug=region_slug,
                    city=city_key,
                    **kwargs,
                )
        else:
            self._scrape_pages(parser, platform_name, max_pages, results, **kwargs)

        # Queue batch embedding for all new vacancies
        if results["created"] > 0:
            try:
                from apps.matching.tasks import backfill_embeddings_task

                backfill_embeddings_task.delay(batch_size=64)
            except Exception:
                logger.debug("Could not queue batch embedding task (Redis/Celery unavailable)")

        logger.info(
            "Scraped %s: %d fetched, %d created, %d dupes, %d invalid, %d errors",
            platform_name,
            results["fetched"],
            results["created"],
            results["skipped_duplicate"],
            results["skipped_invalid"],
            results["errors"],
        )
        return results

    def _scrape_pages(
        self,
        parser,
        platform_name: str,
        max_pages: int,
        results: dict,
        region_slug: str = "",
        consecutive_dup_limit: int = 300,
        **kwargs,
    ) -> None:
        """Inner page loop for a single city/region or a single-region parser.

        Runs until the parser returns an empty page, max_pages is reached,
        or ``consecutive_dup_limit`` consecutive duplicates are hit
        (meaning we've caught up with previously scraped data).
        """
        consecutive_dupes = 0
        cutoff = datetime.now(UTC) - timedelta(days=MAX_VACANCY_AGE_DAYS)

        for page in range(max_pages):
            if page > 0:
                time.sleep(0.5)
            try:
                batch = parser.fetch_page(page=page, **kwargs)
            except Exception:
                logger.exception(
                    "Platform scraper: failed to fetch page %d from %s (city=%s)",
                    page,
                    platform_name,
                    kwargs.get("city", ""),
                )
                results["errors"] += 1
                break

            if not batch:
                break

            results["fetched"] += len(batch)

            # Drop vacancies older than MAX_VACANCY_AGE_DAYS.
            # If the whole page is old, stop — further pages will only be older.
            fresh_batch = []
            for parsed in batch:
                if parsed.posted_at is not None:
                    posted = parsed.posted_at
                    if posted.tzinfo is None:
                        posted = posted.replace(tzinfo=UTC)
                    if posted < cutoff:
                        continue
                fresh_batch.append(parsed)

            if not fresh_batch:
                logger.info(
                    "Stopping %s page %d: entire page is older than %d days",
                    platform_name,
                    page,
                    MAX_VACANCY_AGE_DAYS,
                )
                break

            for parsed in fresh_batch:
                # Inject region from scrape context before normalization
                if region_slug and not parsed.region:
                    parsed.region = region_slug

                parsed = normalize(parsed)

                if not parsed.is_valid:
                    results["skipped_invalid"] += 1
                    continue

                vacancy = self._store_vacancy(parsed, platform_name)
                if vacancy:
                    results["created"] += 1
                    consecutive_dupes = 0
                else:
                    results["skipped_duplicate"] += 1
                    consecutive_dupes += 1

            if consecutive_dupes >= consecutive_dup_limit:
                logger.info(
                    "Stopping %s early: %d consecutive duplicates (caught up)",
                    platform_name,
                    consecutive_dupes,
                )
                break

    @staticmethod
    def _store_vacancy(parsed: ParsedVacancy, platform_name: str) -> Vacancy | None:
        """Store a parsed vacancy. Returns Vacancy if new, None if duplicate.

        A cheap existence check on content_hash runs first so re-scrapes of
        already-known vacancies never reach an INSERT — Postgres logs every
        failed INSERT at ERROR level and that quickly floods the db log on
        scheduled scrapes. The IntegrityError branch remains as a safety net
        for the narrow race window between the check and the create.
        """
        if Vacancy.objects.filter(content_hash=parsed.content_hash).exists():
            return None
        try:
            return Vacancy.objects.create(
                title=parsed.title[:500],
                company=parsed.company[:255],
                description=parsed.description,
                salary_min=parsed.salary_min,
                salary_max=parsed.salary_max,
                salary_currency=parsed.salary_currency[:10],
                employment_type=parsed.employment_type,
                work_format=parsed.work_format,
                location=parsed.location[:255],
                region=parsed.region[:30],
                experience_years=parsed.experience_years,
                skills=parsed.skills,
                contact_info=parsed.contact_info[:500],
                language=parsed.language[:10],
                source=VacancySource.API,
                source_channel=platform_name,
                source_url=parsed.source_url[:500],
                posted_at=parsed.posted_at.replace(tzinfo=UTC)
                if parsed.posted_at and parsed.posted_at.tzinfo is None
                else parsed.posted_at,
                raw_data={},
                content_hash=parsed.content_hash,
            )
        except IntegrityError:
            return None
