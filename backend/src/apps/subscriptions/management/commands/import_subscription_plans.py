"""
Import or update subscription plans.
Usage:
  python manage.py import_subscription_plans
  python manage.py import_subscription_plans --reset
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.subscriptions.models import SubscriptionPlan
from src.apps.subscriptions.management.plans_data import PLANS


class Command(BaseCommand):
    help = "Import or update subscription plans"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing subscription plans before importing",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["reset"]:
            self.stdout.write(self.style.WARNING("Deleting existing plans..."))
            SubscriptionPlan.objects.all().delete()

        self.stdout.write("Importing subscription plans...")

        created_count = 0
        updated_count = 0

        for plan in PLANS:
            obj, created = SubscriptionPlan.objects.update_or_create(
                plan_id=plan["plan_id"],
                defaults=plan,
            )

            if created:
                created_count += 1
                self.stdout.write(f"  Created: {obj.plan_id}")
            else:
                updated_count += 1
                self.stdout.write(f"  Updated: {obj.plan_id}")

        self.stdout.write(
            self.style.SUCCESS(f"Done. Created: {created_count}, Updated: {updated_count}")
        )
