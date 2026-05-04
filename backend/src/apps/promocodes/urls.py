"""Promocodes URLs."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.promocodes.views import PromoCodeUsageViewSet, PromocodeViewSet

router = DefaultRouter()
router.register(r"", PromocodeViewSet, basename="promocode")
router.register(r"usage", PromoCodeUsageViewSet, basename="promocode-usage")

urlpatterns = [
    path("", include(router.urls)),
]
