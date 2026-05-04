"""Analytics API views for admin dashboard."""

import logging
from datetime import timedelta

from django.conf import settings
from django.db.models import Avg, Count, Q, Sum
from django.db.models.functions import TruncDay, TruncHour, TruncMonth, TruncWeek, TruncYear
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from apps.analytics.exchange import get_usd_to_uzs_rate
from apps.analytics.permissions import IsAnalyticsViewer
from apps.resumes.models import Resume
from apps.store.models import CreditTransaction
from apps.subscriptions.models import Subscription
from apps.users.models import User
from apps.vacancies.models import Vacancy

from .models import APICallLog, UserEvent

logger = logging.getLogger(__name__)


def _get_period_filter(request):
    """Parse period query param and return start datetime."""
    period = request.query_params.get("period", "30d")
    now = timezone.now()
    mapping = {
        "1d": timedelta(days=1),
        "7d": timedelta(days=7),
        "30d": timedelta(days=30),
        "90d": timedelta(days=90),
        "1y": timedelta(days=365),
    }
    delta = mapping.get(period, timedelta(days=30))
    return now - delta


def _get_trunc_func(request):
    """Parse granularity query param and return truncation function."""
    granularity = request.query_params.get("granularity", "day")
    return {
        "hour": TruncHour,
        "day": TruncDay,
        "week": TruncWeek,
        "month": TruncMonth,
        "year": TruncYear,
    }.get(granularity, TruncDay)


@api_view(["GET"])
@permission_classes([IsAnalyticsViewer])
def dashboard(request):
    """Aggregated KPI summary."""
    since = _get_period_filter(request)

    total_users = User.objects.count()
    new_users = User.objects.filter(created_at__gte=since).count()
    total_resumes = Resume.objects.count()
    new_resumes = Resume.objects.filter(created_at__gte=since).count()
    active_subs = Subscription.objects.filter(status="active").count()
    total_vacancies = Vacancy.objects.count()

    revenue = (
        CreditTransaction.objects.filter(
            transaction_type="purchase",
            status="completed",
            created_at__gte=since,
        ).aggregate(total=Sum("amount_paid"))["total"]
        or 0
    )

    return Response(
        {
            "total_users": total_users,
            "new_users_period": new_users,
            "total_resumes": total_resumes,
            "new_resumes_period": new_resumes,
            "active_subscriptions": active_subs,
            "total_vacancies": total_vacancies,
            "revenue_period": float(revenue),
        }
    )


@api_view(["GET"])
@permission_classes([IsAnalyticsViewer])
def users_analytics(request):
    """User growth and distribution."""
    since = _get_period_filter(request)
    trunc = _get_trunc_func(request)

    growth = (
        User.objects.filter(created_at__gte=since)
        .annotate(date=trunc("created_at"))
        .values("date")
        .annotate(count=Count("id"))
        .order_by("date")
    )

    growth_by_language = (
        User.objects.filter(created_at__gte=since)
        .annotate(date=trunc("created_at"))
        .values("date", "language")
        .annotate(count=Count("id"))
        .order_by("date")
    )

    language_dist = User.objects.values("language").annotate(count=Count("id")).order_by("-count")

    return Response(
        {
            "growth": list(growth),
            "growth_by_language": list(growth_by_language),
            "language_distribution": list(language_dist),
            "total": User.objects.count(),
        }
    )


@api_view(["GET"])
@permission_classes([IsAnalyticsViewer])
def resumes_analytics(request):
    """Resume creation stats."""
    since = _get_period_filter(request)
    trunc = _get_trunc_func(request)

    by_origin = Resume.objects.values("origin").annotate(count=Count("id")).order_by("-count")

    by_language = Resume.objects.values("language").annotate(count=Count("id")).order_by("-count")

    trend = (
        Resume.objects.filter(created_at__gte=since)
        .annotate(date=trunc("created_at"))
        .values("date")
        .annotate(count=Count("id"))
        .order_by("date")
    )

    return Response(
        {
            "by_origin": list(by_origin),
            "by_language": list(by_language),
            "trend": list(trend),
            "total": Resume.objects.count(),
        }
    )


@api_view(["GET"])
@permission_classes([IsAnalyticsViewer])
def subscriptions_analytics(request):
    """Subscription stats."""
    since = _get_period_filter(request)

    by_status = Subscription.objects.values("status").annotate(count=Count("id")).order_by("-count")

    by_plan = (
        Subscription.objects.filter(status="active")
        .values("plan__name")
        .annotate(count=Count("id"))
        .order_by("-count")
    )

    revenue_trend = (
        CreditTransaction.objects.filter(
            transaction_type="purchase",
            status="completed",
            created_at__gte=since,
        )
        .annotate(date=_get_trunc_func(request)("created_at"))
        .values("date")
        .annotate(revenue=Sum("amount_paid"))
        .order_by("date")
    )

    return Response(
        {
            "by_status": list(by_status),
            "by_plan": list(by_plan),
            "revenue_trend": list(revenue_trend),
            "active_count": Subscription.objects.filter(status="active").count(),
        }
    )


@api_view(["GET"])
@permission_classes([IsAnalyticsViewer])
def credits_analytics(request):
    """Credit transaction stats."""
    since = _get_period_filter(request)
    trunc = _get_trunc_func(request)

    by_type = (
        CreditTransaction.objects.filter(created_at__gte=since)
        .values("transaction_type")
        .annotate(count=Count("id"), total_credits=Sum("credits"))
        .order_by("-count")
    )

    trend = (
        CreditTransaction.objects.filter(created_at__gte=since)
        .annotate(date=trunc("created_at"))
        .values("date", "transaction_type")
        .annotate(count=Count("id"), total=Sum("credits"))
        .order_by("date")
    )

    total_revenue = (
        CreditTransaction.objects.filter(transaction_type="purchase", status="completed").aggregate(
            total=Sum("amount_paid")
        )["total"]
        or 0
    )

    return Response(
        {
            "by_type": list(by_type),
            "trend": list(trend),
            "total_revenue": float(total_revenue),
        }
    )


@api_view(["GET"])
@permission_classes([IsAnalyticsViewer])
def vacancies_analytics(request):
    """Vacancy stats."""
    since = _get_period_filter(request)
    trunc = _get_trunc_func(request)

    trend = (
        Vacancy.objects.filter(created_at__gte=since)
        .annotate(date=trunc("created_at"))
        .values("date")
        .annotate(count=Count("id"))
        .order_by("date")
    )

    by_source = Vacancy.objects.values("source").annotate(count=Count("id")).order_by("-count")

    by_channel = (
        Vacancy.objects.exclude(source_channel="")
        .values("source_channel")
        .annotate(count=Count("id"))
        .order_by("-count")[:15]
    )

    by_type = (
        Vacancy.objects.values("employment_type").annotate(count=Count("id")).order_by("-count")
    )

    from apps.common.regions import get_region_name

    by_region = (
        Vacancy.objects.exclude(region="")
        .values("region")
        .annotate(count=Count("id"))
        .order_by("-count")
    )
    by_region_data = [
        {"region": r["region"], "name": get_region_name(r["region"], "en"), "count": r["count"]}
        for r in by_region
    ]

    # --- salary averages, normalised to UZS ---
    # Treat empty currency as UZS (all sources are Uzbek job boards)
    uzs = Vacancy.objects.filter(
        salary_min__gt=0,
    ).exclude(salary_currency="USD")
    usd = Vacancy.objects.filter(salary_min__gt=0, salary_currency="USD")

    # Cap at reasonable maximums to exclude garbage data
    # UZS: 100M som (~$8K/mo), USD: 20K/mo
    uzs = uzs.filter(salary_min__lte=100_000_000)
    usd = usd.filter(salary_min__lte=20_000)

    uzs_avg = uzs.aggregate(min=Avg("salary_min"), max=Avg("salary_max"), n=Count("id"))
    usd_avg = usd.aggregate(min=Avg("salary_min"), max=Avg("salary_max"), n=Count("id"))

    rate = get_usd_to_uzs_rate()
    uzs_n = uzs_avg["n"] or 0
    usd_n = usd_avg["n"] or 0
    total_n = uzs_n + usd_n

    if total_n > 0:
        uzs_min_sum = (uzs_avg["min"] or 0) * uzs_n + (usd_avg["min"] or 0) * rate * usd_n
        uzs_max_sum = (uzs_avg["max"] or 0) * uzs_n + (usd_avg["max"] or 0) * rate * usd_n
        avg_min = uzs_min_sum / total_n
        avg_max = uzs_max_sum / total_n
    else:
        avg_min = avg_max = 0

    # --- human-readable source names ---
    source_names = {}
    for key, cfg in getattr(settings, "TELEGRAM_JOB_CHANNELS", {}).items():
        source_names[key] = cfg.get("name", key)
    for key, cfg in getattr(settings, "PLATFORM_SOURCES", {}).items():
        source_names[key] = cfg.get("name", key)

    return Response(
        {
            "trend": list(trend),
            "by_source": list(by_source),
            "by_channel": list(by_channel),
            "by_employment_type": list(by_type),
            "by_region": by_region_data,
            "avg_salary": {
                "min": round(avg_min),
                "max": round(avg_max),
                "currency": "UZS",
            },
            "source_names": source_names,
            "total": Vacancy.objects.count(),
        }
    )


@api_view(["GET"])
@permission_classes([IsAnalyticsViewer])
def referrals_analytics(request):
    """Referral stats."""
    from apps.referrals.models import Referral, ReferralSignup

    total_referrals = ReferralSignup.objects.count()
    active_referrers = Referral.objects.filter(total_referrals__gt=0).count()
    total_commission = Referral.objects.aggregate(total=Sum("total_commission"))["total"] or 0

    top_referrers = (
        Referral.objects.filter(total_referrals__gt=0)
        .select_related("user")
        .values("user__username", "total_referrals", "total_commission")
        .order_by("-total_referrals")[:10]
    )

    return Response(
        {
            "total_signups": total_referrals,
            "active_referrers": active_referrers,
            "total_commission": float(total_commission),
            "top_referrers": list(top_referrers),
        }
    )


@api_view(["GET"])
@permission_classes([IsAnalyticsViewer])
def api_usage(request):
    """External API usage stats."""
    since = _get_period_filter(request)
    trunc = _get_trunc_func(request)

    by_provider = (
        APICallLog.objects.filter(created_at__gte=since)
        .values("provider")
        .annotate(
            count=Count("id"),
            total_tokens=Sum("tokens_used"),
            total_cost=Sum("cost"),
            avg_response_ms=Avg("response_time_ms"),
            error_count=Count("id", filter=Q(success=False)),
        )
        .order_by("-count")
    )

    trend = (
        APICallLog.objects.filter(created_at__gte=since)
        .annotate(date=trunc("created_at"))
        .values("date", "provider")
        .annotate(count=Count("id"), tokens=Sum("tokens_used"), cost=Sum("cost"))
        .order_by("date")
    )

    return Response(
        {
            "by_provider": list(by_provider),
            "trend": list(trend),
            "total_calls": APICallLog.objects.filter(created_at__gte=since).count(),
        }
    )


@api_view(["GET"])
@permission_classes([IsAnalyticsViewer])
def health(request):
    """System health checks."""
    checks = {}

    # Database
    try:
        User.objects.exists()
        checks["database"] = {"status": "ok"}
    except Exception as e:
        checks["database"] = {"status": "error", "message": str(e)}

    # Redis
    try:
        from django.core.cache import cache

        cache.set("health_check", "ok", 5)
        val = cache.get("health_check")
        checks["redis"] = {"status": "ok" if val == "ok" else "error"}
    except Exception as e:
        checks["redis"] = {"status": "error", "message": str(e)}

    # Celery
    try:
        from config.celery import app as celery_app

        insp = celery_app.control.inspect(timeout=3)
        ping = insp.ping()
        checks["celery"] = {
            "status": "ok" if ping else "warning",
            "workers": len(ping) if ping else 0,
        }
    except Exception as e:
        logger.warning("Celery health check failed: %s", str(e))
        checks["celery"] = {"status": "unknown", "message": "Could not inspect workers"}

    # Server resources
    resources = {}
    try:
        import psutil

        resources["cpu_percent"] = psutil.cpu_percent(interval=0.5)
        mem = psutil.virtual_memory()
        resources["memory"] = {
            "total_gb": round(mem.total / (1024**3), 1),
            "used_gb": round(mem.used / (1024**3), 1),
            "percent": mem.percent,
        }
        disk = psutil.disk_usage("/")
        resources["disk"] = {
            "total_gb": round(disk.total / (1024**3), 1),
            "used_gb": round(disk.used / (1024**3), 1),
            "percent": disk.percent,
        }
    except ImportError:
        resources = None
    except Exception as e:
        logger.warning("Could not collect server resources: %s", str(e))
        resources = None

    all_ok = all(c.get("status") == "ok" for c in checks.values())

    return Response(
        {
            "status": "healthy" if all_ok else "degraded",
            "checks": checks,
            "resources": resources,
        }
    )


@api_view(["POST"])
@permission_classes([])  # ApiKeyAuthentication already validates the key
def track_event(request):
    """Record a user event from the telegram bot."""
    event_type = request.data.get("event_type")
    telegram_id = request.data.get("telegram_id")

    if not event_type or not telegram_id:
        return Response({"error": "event_type and telegram_id required"}, status=400)

    UserEvent.objects.create(
        event_type=event_type,
        telegram_id=telegram_id,
        metadata=request.data.get("metadata", {}),
    )
    return Response({"status": "ok"}, status=201)


@api_view(["GET"])
@permission_classes([IsAnalyticsViewer])
def user_events_analytics(request):
    """User event analytics (e.g., job feed scrolls)."""
    since = _get_period_filter(request)
    trunc = _get_trunc_func(request)
    event_type = request.query_params.get("event_type", "job_feed_scroll")

    trend = (
        UserEvent.objects.filter(created_at__gte=since, event_type=event_type)
        .annotate(date=trunc("created_at"))
        .values("date")
        .annotate(count=Count("id"))
        .order_by("date")
    )

    total = UserEvent.objects.filter(created_at__gte=since, event_type=event_type).count()

    return Response(
        {
            "trend": list(trend),
            "total": total,
            "event_type": event_type,
        }
    )


@api_view(["GET"])
@permission_classes([IsAnalyticsViewer])
def active_users_analytics(request):
    """Distinct users who triggered any event per time slot."""
    since = _get_period_filter(request)
    trunc = _get_trunc_func(request)

    trend = (
        UserEvent.objects.filter(created_at__gte=since)
        .annotate(date=trunc("created_at"))
        .values("date")
        .annotate(count=Count("telegram_id", distinct=True))
        .order_by("date")
    )

    total = UserEvent.objects.filter(created_at__gte=since).values("telegram_id").distinct().count()

    return Response({"trend": list(trend), "total": total})
