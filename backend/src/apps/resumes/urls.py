"""Resume URLs."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.resumes import views

# Router for all resume operations
router = DefaultRouter()
router.register(r"", views.ResumeViewSet, basename="resume")

urlpatterns = [
    path("", include(router.urls)),
]
