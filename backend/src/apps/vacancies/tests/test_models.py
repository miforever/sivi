"""Vacancy app tests."""

import pytest
from rest_framework.test import APIClient

from apps.vacancies.models import Vacancy


@pytest.mark.django_db
class TestVacancyAPI:
    """Test vacancy API endpoints."""

    def test_get_vacancy_detail(self):
        """Test getting vacancy detail."""
        vacancy = Vacancy.objects.create(
            title="Backend Developer",
            company="Tech Corp",
            description="We are looking for experienced backend developers",
        )
        client = APIClient()
        response = client.get(f"/api/v1/vacancies/{vacancy.id}/")
        assert response.status_code == 200
        assert response.data["title"] == "Backend Developer"
