# src/config/celery.py
import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

app = Celery("sivi")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    # --- Telegram channels: every 2 hours ---
    "scrape-all-channels": {
        "task": "apps.vacancies.tasks.scrape_all_channels_task",
        "schedule": crontab(minute=0, hour="*/2"),
    },
    # --- hh.uz: every 2 hours (most active source, stops on duplicates) ---
    "scrape-hh-uz": {
        "task": "apps.vacancies.tasks.scrape_platform_task",
        "schedule": crontab(minute=10, hour="*/2"),
        "kwargs": {"platform_name": "hh_uz"},
    },
    # --- olx.uz: every 2 hours ---
    "scrape-olx-uz": {
        "task": "apps.vacancies.tasks.scrape_platform_task",
        "schedule": crontab(minute=20, hour="*/2"),
        "kwargs": {"platform_name": "olx_uz"},
    },
    # --- vacandi.uz: every 2 hours ---
    "scrape-vacandi-uz": {
        "task": "apps.vacancies.tasks.scrape_platform_task",
        "schedule": crontab(minute=25, hour="*/2"),
        "kwargs": {"platform_name": "vacandi_uz"},
    },
    # --- ishkop.uz: every 2 hours ---
    "scrape-ishkop-uz": {
        "task": "apps.vacancies.tasks.scrape_platform_task",
        "schedule": crontab(minute=30, hour="*/2"),
        "kwargs": {"platform_name": "ishkop_uz"},
    },
    # --- argos.uz (civil service): every 2 hours ---
    "scrape-argos-uz": {
        "task": "apps.vacancies.tasks.scrape_platform_task",
        "schedule": crontab(minute=35, hour="*/2"),
        "kwargs": {"platform_name": "argos_uz"},
    },
    # --- osonish.uz: every 2 hours ---
    "scrape-osonish-uz": {
        "task": "apps.vacancies.tasks.scrape_platform_task",
        "schedule": crontab(minute=40, hour="*/2"),
        "kwargs": {"platform_name": "osonish_uz"},
    },
    # --- ish.uz: every 2 hours ---
    "scrape-ish-uz": {
        "task": "apps.vacancies.tasks.scrape_platform_task",
        "schedule": crontab(minute=45, hour="*/2"),
        "kwargs": {"platform_name": "ish_uz"},
    },
    # --- ishplus.uz: every 2 hours ---
    "scrape-ishplus-uz": {
        "task": "apps.vacancies.tasks.scrape_platform_task",
        "schedule": crontab(minute=50, hour="*/2"),
        "kwargs": {"platform_name": "ishplus_uz"},
    },
    # --- Uzbekistan Airways: daily (small, finite vacancy set) ---
    "scrape-uzairways": {
        "task": "apps.vacancies.tasks.scrape_platform_task",
        "schedule": crontab(minute=5, hour=2),
        "kwargs": {"platform_name": "uzairways"},
    },
    # --- Embeddings backfill: 15 min after each scrape ---
    "backfill-embeddings": {
        "task": "apps.matching.tasks.backfill_embeddings_task",
        "schedule": crontab(minute=15, hour="*/2"),
    },
    # --- Purge stale vacancies: daily at 4:00 AM ---
    "purge-stale-vacancies": {
        "task": "apps.vacancies.tasks.purge_stale_vacancies_task",
        "schedule": crontab(minute=0, hour=4),
    },
    # --- Purge old vacancy impressions: daily at 4:30 AM ---
    "purge-old-impressions": {
        "task": "apps.matching.tasks.purge_old_impressions_task",
        "schedule": crontab(minute=30, hour=4),
    },
}
