"""Delete vacancies older than a given number of days (default: 60)."""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.vacancies.models import Vacancy


class Command(BaseCommand):
    help = "Delete vacancies whose posted_at is older than N days (default 60)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=60,
            help="Delete vacancies older than this many days (default: 60).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print how many would be deleted without actually deleting.",
        )

    def handle(self, *args, **options):
        days = options["days"]
        dry_run = options["dry_run"]

        cutoff = timezone.now() - timedelta(days=days)
        qs = Vacancy.objects.filter(posted_at__lt=cutoff)
        count = qs.count()

        if dry_run:
            self.stdout.write(
                f"[dry-run] Would delete {count} vacancies posted before {cutoff.date()}."
            )
            return

        deleted, _ = qs.delete()
        self.stdout.write(
            self.style.SUCCESS(f"Deleted {deleted} vacancies posted before {cutoff.date()}.")
        )
