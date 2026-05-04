"""
Main URL configuration for resume-vacancy-api project.
"""

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),
    # API Schema
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("swagger/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    # API endpoints
    path(
        "api/v1/",
        include(
            [
                # JWT Authentication
                path("auth/token/", TokenObtainPairView.as_view(), name="token-obtain"),
                path("auth/token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
                # App endpoints
                path("questions/", include("apps.questions.urls")),
                path("user/", include("apps.users.urls")),
                path("resumes/", include("apps.resumes.urls")),
                path("subscriptions/", include("apps.subscriptions.urls")),
                path("promocodes/", include("apps.promocodes.urls")),
                path("referrals/", include("apps.referrals.urls")),
                path("vacancies/", include("apps.vacancies.urls")),
                path("matching/", include("apps.matching.urls")),
                # Analytics (admin-only)
                path("analytics/", include("apps.analytics.urls")),
            ]
        ),
    ),
]
