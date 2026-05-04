"""Vacancy views."""

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.throttling import AnonRateThrottle

from apps.vacancies.models import Vacancy
from apps.vacancies.serializers import VacancyDetailSerializer, VacancyListSerializer


class VacancySearchThrottle(AnonRateThrottle):
    scope = "vacancy_search"


class VacancyViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for browsing aggregated job vacancies."""

    queryset = Vacancy.objects.all()
    permission_classes = [AllowAny]
    throttle_classes = [VacancySearchThrottle]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        "employment_type",
        "work_format",
        "country",
        "region",
        "source_channel",
        "language",
        "salary_currency",
    ]
    search_fields = ["title", "company", "description", "location"]
    ordering_fields = ["posted_at", "created_at", "salary_min"]

    def get_serializer_class(self):
        if self.action == "list":
            return VacancyListSerializer
        return VacancyDetailSerializer
