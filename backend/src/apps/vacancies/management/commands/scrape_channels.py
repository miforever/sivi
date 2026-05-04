"""Management command to scrape all configured Telegram channels."""

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.vacancies.scraper.service import ScraperService


class Command(BaseCommand):
    help = "Scrape all configured Telegram channels for job vacancies."

    def add_arguments(self, parser):
        parser.add_argument(
            "--channel",
            type=str,
            help="Scrape a single channel by username.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=200,
            help="Max messages per channel for first-time backfill (default: 200). Ignored on incremental runs.",
        )

    def handle(self, *args, **options):
        service = ScraperService()
        limit = options["limit"]
        channel = options.get("channel")

        if channel:
            channels = [channel]
        else:
            channels = list(settings.TELEGRAM_JOB_CHANNELS.keys())

        self.stdout.write(f"Scraping {len(channels)} channel(s) (limit={limit})...\n")

        total_created = 0
        for username in channels:
            self.stdout.write(f"  @{username} ... ", ending="")
            try:
                result = service.scrape_channel(username, limit=limit)
                created = result.get("created", 0)
                total_created += created
                self.stdout.write(
                    f"fetched={result['fetched']} "
                    f"created={created} "
                    f"dupes={result['skipped_duplicate']} "
                    f"skip={result['skipped_not_vacancy']} "
                    f"err={result['errors']}"
                )
            except Exception as exc:
                self.stderr.write(f"FAILED: {exc}")

        self.stdout.write(f"\nDone. {total_created} new vacancies created.")
