"""Celery tasks for embedding generation and matching housekeeping."""

import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def generate_vacancy_embedding_task(self, vacancy_id: str):
    """Generate embedding for a single vacancy."""
    from apps.matching.services.matcher import MatcherService
    from apps.vacancies.models import Vacancy

    try:
        vacancy = Vacancy.objects.get(id=vacancy_id)
        if vacancy.embedding is not None:
            return
        service = MatcherService()
        service.generate_vacancy_embedding(vacancy)
    except Vacancy.DoesNotExist:
        logger.warning("Vacancy %s not found for embedding", vacancy_id)
    except Exception as exc:
        logger.exception("Failed to generate embedding for vacancy %s", vacancy_id)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def generate_resume_embedding_task(self, resume_id: str):
    """Generate embedding for a resume."""
    from apps.matching.services.embedding import get_embedding_service, prepare_resume_text
    from apps.resumes.models import Resume

    try:
        resume = Resume.objects.get(id=resume_id)
        if resume.embedding is not None:
            return
        service = get_embedding_service()
        resume_text = prepare_resume_text(resume)
        embedding = service.embed([resume_text])[0]
        resume.embedding = embedding
        resume.save(update_fields=["embedding"])
        logger.info("Generated embedding for resume %s", resume_id)
    except Resume.DoesNotExist:
        logger.warning("Resume %s not found for embedding", resume_id)
    except Exception as exc:
        logger.exception("Failed to generate embedding for resume %s", resume_id)
        raise self.retry(exc=exc)


@shared_task
def backfill_embeddings_task(batch_size: int = 32):
    """Backfill embeddings for vacancies that don't have one.

    Processes one batch, then re-queues itself if more remain.
    """
    from apps.matching.services.matcher import MatcherService
    from apps.vacancies.models import Vacancy

    vacancies = list(Vacancy.objects.filter(embedding=None)[:batch_size])
    if not vacancies:
        logger.info("Backfill complete — no vacancies without embeddings")
        return

    service = MatcherService()
    count = service.generate_vacancy_embeddings_batch(vacancies)
    logger.info("Backfilled %d vacancy embeddings", count)

    # Check if more remain
    remaining = Vacancy.objects.filter(embedding=None).count()
    if remaining > 0:
        logger.info("Backfill: %d vacancies remaining, re-queuing", remaining)
        backfill_embeddings_task.delay(batch_size)


@shared_task
def purge_old_impressions_task(days: int = 30):
    """Delete VacancyImpression rows older than `days` days.

    Matching uses a 14-day window on impressions for "already seen" filtering,
    so rows older than that are dead weight.
    """
    from apps.matching.models import VacancyImpression

    cutoff = timezone.now() - timedelta(days=days)
    deleted, _ = VacancyImpression.objects.filter(shown_at__lt=cutoff).delete()
    logger.info("Purged %d vacancy impressions older than %d days", deleted, days)
    return deleted
