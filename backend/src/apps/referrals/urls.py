"""Referrals URLs."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.referrals.views import ReferralViewSet

router = DefaultRouter()
router.register(r"", ReferralViewSet, basename="referral")

urlpatterns = [
    path("", include(router.urls)),
]
