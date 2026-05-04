"""Scraper orchestration service: fetch → parse → store."""

import asyncio
import logging
from datetime import UTC, datetime, timedelta

from asgiref.sync import sync_to_async
from django.conf import settings
from django.db import IntegrityError

from apps.vacancies.models import ScrapeState, Vacancy
from apps.vacancies.scraper.base import ParsedVacancy
from apps.vacancies.scraper.channels import get_parser
from apps.vacancies.scraper.client import get_client
from apps.vacancies.scraper.fetcher import fetch_channel_messages
from apps.vacancies.scraper.normalizer import normalize

MAX_VACANCY_AGE_DAYS = 60

logger = logging.getLogger(__name__)


class ScraperService:
    """Orchestrates the scraping pipeline for a single channel."""

    def scrape_channel(self, channel_username: str, limit: int = 50) -> dict:
        """Scrape a channel: fetch messages, parse vacancies, store new ones.

        Returns a summary dict with counts.
        """
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(self._async_scrape(channel_username, limit))
        finally:
            loop.close()

    async def _async_scrape(self, channel_username: str, limit: int) -> dict:
        """Async scraping pipeline."""
        client = get_client()

        results = {
            "channel": channel_username,
            "fetched": 0,
            "created": 0,
            "skipped_not_vacancy": 0,
            "skipped_duplicate": 0,
            "errors": 0,
        }

        try:
            await client.connect()
            if not await client.is_user_authorized():
                logger.error("Telethon session expired for channel %s", channel_username)
                return results

            # Get last scraped message ID for incremental fetching
            min_id = await sync_to_async(self._get_last_message_id)(channel_username)

            # For incremental runs, fetch everything since the cursor (no cap).
            # For first-time backfill (min_id=0), respect the provided limit.
            effective_limit = None if min_id > 0 else limit
            raw_messages = await fetch_channel_messages(
                client,
                channel_username,
                limit=effective_limit,
                min_id=min_id,
            )
            results["fetched"] = len(raw_messages)

            # Drop messages older than MAX_VACANCY_AGE_DAYS
            cutoff = datetime.now(UTC) - timedelta(days=MAX_VACANCY_AGE_DAYS)
            fresh_messages = []
            for msg in raw_messages:
                date_str = msg.get("date")
                if date_str:
                    try:
                        msg_date = datetime.fromisoformat(date_str)
                        if msg_date.tzinfo is None:
                            msg_date = msg_date.replace(tzinfo=UTC)
                        if msg_date < cutoff:
                            continue
                    except (ValueError, TypeError):
                        pass
                fresh_messages.append(msg)
            raw_messages = fresh_messages

        except Exception:
            logger.exception("Failed to fetch messages from @%s", channel_username)
            results["errors"] += 1
            return results
        finally:
            await client.disconnect()

        if not raw_messages:
            return results

        parser = get_parser(channel_username)

        # Get channel language from config
        channel_config = settings.TELEGRAM_JOB_CHANNELS.get(channel_username, {})
        channel_language = channel_config.get("language", "")

        max_message_id = min_id
        for msg in raw_messages:
            msg_id = msg.get("id", 0)
            max_message_id = max(max_message_id, msg_id)

            try:
                parsed = parser.parse(msg)
            except Exception:
                logger.exception("Parse error for message %d in @%s", msg_id, channel_username)
                results["errors"] += 1
                continue

            if parsed is None:
                results["skipped_not_vacancy"] += 1
                continue

            # Set language from channel config
            if channel_language:
                parsed.language = channel_language

            # Normalize to uniform format before storage
            parsed = normalize(parsed)

            if not parsed.is_valid:
                results["skipped_not_vacancy"] += 1
                continue

            vacancy = await sync_to_async(self._store_vacancy)(parsed, channel_username, msg)
            if vacancy:
                results["created"] += 1
            else:
                results["skipped_duplicate"] += 1

        # Queue batch embedding for all new vacancies
        if results["created"] > 0:
            try:
                from apps.matching.tasks import backfill_embeddings_task

                backfill_embeddings_task.delay(batch_size=64)
            except Exception:
                logger.debug("Could not queue batch embedding task (Redis/Celery not available)")

        # Update scrape state
        if max_message_id > min_id:
            await sync_to_async(self._update_last_message_id)(channel_username, max_message_id)

        logger.info(
            "Scraped @%s: %d fetched, %d created, %d dupes, %d not_vacancy, %d errors",
            channel_username,
            results["fetched"],
            results["created"],
            results["skipped_duplicate"],
            results["skipped_not_vacancy"],
            results["errors"],
        )

        return results

    @staticmethod
    def _store_vacancy(parsed: ParsedVacancy, channel_username: str, raw_msg: dict):
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
                source="telegram",
                source_channel=channel_username,
                source_message_id=raw_msg.get("id"),
                source_url=parsed.source_url[:500],
                posted_at=parsed.posted_at.replace(tzinfo=UTC)
                if parsed.posted_at and parsed.posted_at.tzinfo is None
                else parsed.posted_at,
                raw_data=raw_msg,
                content_hash=parsed.content_hash,
            )
        except IntegrityError:
            # Duplicate: either same channel+message_id or same content_hash
            return None

    @staticmethod
    def _get_last_message_id(channel_username: str) -> int:
        """Get the last scraped message ID for incremental fetching."""
        try:
            state = ScrapeState.objects.get(channel_username=channel_username)
            return state.last_message_id
        except ScrapeState.DoesNotExist:
            return 0

    @staticmethod
    def _update_last_message_id(channel_username: str, message_id: int):
        """Update the last scraped message ID."""
        ScrapeState.objects.update_or_create(
            channel_username=channel_username,
            defaults={"last_message_id": message_id},
        )
