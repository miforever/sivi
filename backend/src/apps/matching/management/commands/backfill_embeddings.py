"""Management command to backfill embeddings for existing vacancies."""

import logging
import time

from django.core.management.base import BaseCommand

from apps.matching.services.matcher import MatcherService
from apps.vacancies.models import Vacancy

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Backfill embeddings for vacancies that don't have one"

    def add_arguments(self, parser):
        parser.add_argument(
            "--batch-size",
            type=int,
            default=32,
            help="Number of vacancies to embed per API call (default: 32)",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=0,
            help="Max vacancies to process, 0 = all (default: 0)",
        )
        parser.add_argument(
            "--delay",
            type=float,
            default=0.5,
            help="Seconds to wait between batches (default: 0.5)",
        )

    def handle(self, *args, **options):
        batch_size = options["batch_size"]
        limit = options["limit"]
        delay = options["delay"]

        total_missing = Vacancy.objects.filter(embedding=None).count()
        if total_missing == 0:
            self.stdout.write(self.style.SUCCESS("All vacancies already have embeddings."))
            return

        target = min(total_missing, limit) if limit > 0 else total_missing
        self.stdout.write(f"Backfilling {target} of {total_missing} vacancies...")

        service = MatcherService()
        processed = 0

        while processed < target:
            remaining = target - processed
            current_batch_size = min(batch_size, remaining)

            vacancies = list(Vacancy.objects.filter(embedding=None)[:current_batch_size])
            if not vacancies:
                break

            count = service.generate_vacancy_embeddings_batch(vacancies)
            processed += count
            self.stdout.write(f"  Processed {processed}/{target}")

            if processed < target:
                time.sleep(delay)

        self.stdout.write(self.style.SUCCESS(f"Done. Backfilled {processed} vacancy embeddings."))
