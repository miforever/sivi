"""Management command to scrape all registered job platforms."""

from django.core.management.base import BaseCommand

from apps.vacancies.scraper.platforms import PLATFORM_REGISTRY
from apps.vacancies.scraper.platforms.service import PlatformScraperService


class Command(BaseCommand):
    help = "Scrape job platforms (e.g. hh_uz) for vacancies."

    def add_arguments(self, parser):
        parser.add_argument(
            "--platform",
            type=str,
            help="Scrape a single platform by name (e.g. hh_uz).",
        )
        parser.add_argument(
            "--max-pages",
            type=int,
            default=1000,
            help="Safety cap on pages per platform (default: 1000). Stops earlier on 50 consecutive duplicates.",
        )
        parser.add_argument(
            "--text",
            type=str,
            default="",
            help="Optional keyword filter forwarded to the platform API.",
        )

    def handle(self, *args, **options):
        service = PlatformScraperService()
        max_pages = options["max_pages"]
        text = options["text"]
        platform = options.get("platform")

        platforms = [platform] if platform else list(PLATFORM_REGISTRY.keys())
        self.stdout.write(
            f"Scraping {len(platforms)} platform(s) "
            f"(max_pages={max_pages}" + (f', text="{text}"' if text else "") + ")...\n"
        )

        total_created = 0
        for name in platforms:
            self.stdout.write(f"  {name} ... ", ending="")
            kwargs = {"text": text} if text else {}
            try:
                result = service.scrape_platform(name, max_pages=max_pages, **kwargs)
                created = result.get("created", 0)
                total_created += created
                self.stdout.write(
                    f"fetched={result['fetched']} "
                    f"created={created} "
                    f"dupes={result['skipped_duplicate']} "
                    f"invalid={result['skipped_invalid']} "
                    f"err={result['errors']}"
                )
            except Exception as exc:
                self.stderr.write(f"FAILED: {exc}")

        self.stdout.write(f"\nDone. {total_created} new vacancies created.")
