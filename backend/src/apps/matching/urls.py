"""Matching URLs."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.matching.views import MatchingViewSet

router = DefaultRouter()
router.register(r"", MatchingViewSet, basename="matching")

urlpatterns = [
    path("", include(router.urls)),
]
