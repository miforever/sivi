"""Matching views."""

import logging
from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from apps.common.authentication import TelegramBotAuthentication
from apps.common.responses import error_response, success_response
from apps.matching.models import VacancyImpression
from apps.matching.serializers import MatchedVacancySerializer, MatchRequestSerializer
from apps.matching.services.matcher import MatcherService
from apps.resumes.models import Resume

logger = logging.getLogger(__name__)


class MatchingViewSet(viewsets.ViewSet):
    """Semantic job matching endpoints."""

    authentication_classes = [TelegramBotAuthentication]
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["post"], url_path="find-jobs")
    def find_jobs(self, request):
        """Find vacancies matching a user's resume.

        POST /api/v1/matching/find-jobs/
        """
        serializer = MatchRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        resume_id = serializer.validated_data["resume_id"]
        limit = serializer.validated_data["limit"]
        filters = serializer.validated_data.get("filters", {})
        exclude_ids = list(serializer.validated_data.get("exclude_ids", []))

        # Auto-inject user's preferred regions if not explicitly overridden
        if "regions" not in filters and getattr(request.user, "preferred_regions", None):
            filters["regions"] = request.user.preferred_regions

        try:
            resume = Resume.objects.get(id=resume_id, user=request.user)
        except Resume.DoesNotExist:
            return error_response(
                code="RESUME_NOT_FOUND",
                message="Resume not found or does not belong to you",
                status_code=404,
            )

        # "Already seen" filter — excludes vacancies shown to this user in the
        # last 14 days so the feed doesn't replay the same matches while still
        # letting the candidate pool refill over time.
        impression_cutoff = timezone.now() - timedelta(days=14)
        seen_ids = list(
            VacancyImpression.objects.filter(
                user=request.user,
                shown_at__gte=impression_cutoff,
            ).values_list("vacancy_id", flat=True)
        )
        if seen_ids:
            exclude_ids = list({*exclude_ids, *seen_ids})

        service = MatcherService()
        vacancies = service.find_matching_vacancies(
            resume=resume,
            limit=limit,
            filters=filters,
            exclude_ids=exclude_ids,
        )

        # Record impressions for returned vacancies so subsequent calls skip them
        if vacancies:
            with transaction.atomic():
                VacancyImpression.objects.bulk_create(
                    [VacancyImpression(user=request.user, vacancy_id=v.id) for v in vacancies],
                    ignore_conflicts=True,
                )

        result_serializer = MatchedVacancySerializer(vacancies, many=True)
        return success_response(data=result_serializer.data)
