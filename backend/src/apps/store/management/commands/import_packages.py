# apps/store/management/commands/import_packages.py
"""Management command to import credit packages into database."""

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.store.management.credit_packages import RESUME_CREDIT_PACKS
from apps.store.models import CreditPackage


class Command(BaseCommand):
    help = "Import credit packages from configuration into database"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing packages before importing",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["clear"]:
            deleted_count = CreditPackage.objects.all().delete()[0]
            self.stdout.write(self.style.WARNING(f"Deleted {deleted_count} existing packages"))

        created_count = 0
        updated_count = 0

        for pack_id, pack_data in RESUME_CREDIT_PACKS.items():
            package, created = CreditPackage.objects.update_or_create(
                credits=pack_data["credits"],
                defaults={
                    "price": pack_data["price"],
                    "currency": pack_data["currency"],
                    "is_active": True,
                },
            )

            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✓ Created: {package.credits} credits - {package.price} {package.currency}"
                    )
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"↻ Updated: {package.credits} credits - {package.price} {package.currency}"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✓ Import completed: {created_count} created, {updated_count} updated"
            )
        )
