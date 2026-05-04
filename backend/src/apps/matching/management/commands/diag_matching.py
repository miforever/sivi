"""Diagnose why a user is seeing few matching results."""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db.models import Count, Q
from django.utils import timezone

from apps.matching.models import VacancyImpression
from apps.vacancies.models import Vacancy

User = get_user_model()


class Command(BaseCommand):
    help = "Diagnose matching pool size and impression history for a user"

    def add_arguments(self, parser):
        parser.add_argument(
            "--telegram-id",
            type=int,
            default=None,
            help="Defaults to the first superuser in the DB",
        )
        parser.add_argument("--days", type=int, default=14)
        parser.add_argument(
            "--purge",
            action="store_true",
            help="Delete ALL VacancyImpression rows for this user (destructive)",
        )

    def handle(self, *args, **opts):
        qs = Vacancy.objects.exclude(embedding=None)

        self.stdout.write(f"vacancies total          = {Vacancy.objects.count()}")
        self.stdout.write(f"vacancies with embedding = {qs.count()}")
        self.stdout.write("")

        by_region = qs.values("region").order_by("region").annotate(n=Count("id"))
        self.stdout.write("embedded vacancies by region:")
        for row in by_region:
            self.stdout.write(f"  {row['region'] or '(empty)':20s} {row['n']}")

        # Per-user pool narrowing (optional)
        if not opts["telegram_id"]:
            return

        try:
            user = User.objects.get(telegram_id=opts["telegram_id"])
        except User.DoesNotExist:
            self.stderr.write(f"User with telegram_id={opts['telegram_id']} not found")
            return

        cutoff = timezone.now() - timedelta(days=opts["days"])
        regions = getattr(user, "preferred_regions", None) or []

        if regions:
            qs_region = qs.filter(Q(region__in=regions) | Q(work_format="remote") | Q(region=""))
        else:
            qs_region = qs

        seen_ids = list(
            VacancyImpression.objects.filter(user=user, shown_at__gte=cutoff).values_list(
                "vacancy_id", flat=True
            )
        )

        self.stdout.write("")
        self.stdout.write(f"user telegram_id             = {user.telegram_id}")
        self.stdout.write(f"user preferred_regions       = {regions}")
        self.stdout.write(
            f"impressions total (all time) = {VacancyImpression.objects.filter(user=user).count()}"
        )
        self.stdout.write(f"impressions last {opts['days']}d           = {len(seen_ids)}")
        self.stdout.write(f"pool after region filter     = {qs_region.count()}")
        self.stdout.write(
            f"pool after impression excl.  = {qs_region.exclude(id__in=seen_ids).count()}"
        )

        if opts["purge"]:
            deleted, _ = VacancyImpression.objects.filter(user=user).delete()
            self.stdout.write(self.style.WARNING(f"\nPurged {deleted} impressions for this user"))
