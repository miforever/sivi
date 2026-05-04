"""Vacancy URLs."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.vacancies.views import VacancyViewSet

router = DefaultRouter()
router.register(r"", VacancyViewSet, basename="vacancy")

urlpatterns = [
    path("", include(router.urls)),
]
