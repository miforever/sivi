"""Management command: backfill region slugs for existing vacancies."""

from django.core.management.base import BaseCommand

from apps.common.regions import resolve_region
from apps.vacancies.models import Vacancy


class Command(BaseCommand):
    help = "Backfill the region field for vacancies that have location but no region set."

    def add_arguments(self, parser):
        parser.add_argument(
            "--batch-size",
            type=int,
            default=500,
            help="Number of vacancies to process per batch (default: 500)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print counts without saving",
        )

    def handle(self, *args, **options):
        batch_size = options["batch_size"]
        dry_run = options["dry_run"]

        qs = Vacancy.objects.filter(region="").exclude(location="").order_by("id")
        total = qs.count()
        self.stdout.write(f"Found {total} vacancies with location but no region.")

        if dry_run:
            self.stdout.write("Dry run — no changes saved.")
            return

        updated = 0
        skipped = 0
        batch = []

        for vacancy in qs.iterator(chunk_size=batch_size):
            slug = resolve_region(vacancy.location)
            if slug:
                vacancy.region = slug
                batch.append(vacancy)
                updated += 1
            else:
                skipped += 1

            if len(batch) >= batch_size:
                Vacancy.objects.bulk_update(batch, ["region"])
                self.stdout.write(f"  {updated} updated so far...")
                batch = []

        if batch:
            Vacancy.objects.bulk_update(batch, ["region"])

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. Updated: {updated}, could not resolve: {skipped} (out of {total})"
            )
        )
