"""Integration tests for API."""

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


@pytest.mark.django_db
class TestAPIIntegration:
    """Integration tests for the API."""

    def setup_method(self):
        """Set up test fixtures."""
        settings.API_KEYS = ["test-api-key"]
        self.client = APIClient()
        self.client.credentials(HTTP_X_API_KEY="test-api-key")
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", first_name="Test", last_name="User"
        )

    def test_api_health(self):
        """Test that API is responding."""
        response = self.client.get("/swagger/")
        assert response.status_code == 200

    def test_user_registration(self):
        """Test complete user registration flow."""
        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "first_name": "New",
            "last_name": "User",
        }
        response = self.client.post("/api/v1/user/", data)
        assert response.status_code == 201
        assert User.objects.count() == 2  # Initial + new
