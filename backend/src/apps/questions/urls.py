"""Question URLs."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.questions.views import QuestionViewSet

router = DefaultRouter()
router.register(r"", QuestionViewSet, basename="question")

urlpatterns = [
    path("", include(router.urls)),
]
