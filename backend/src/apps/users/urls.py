"""User URLs."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.users.views import TelegramUserViewSet, UserViewSet

user_router = DefaultRouter()
user_router.register(r"", UserViewSet, basename="user")

telegram_router = DefaultRouter()
telegram_router.register(r"", TelegramUserViewSet, basename="telegram-user")

urlpatterns = [
    path("telegram/", include(telegram_router.urls)),
    path("", include(user_router.urls)),
]
