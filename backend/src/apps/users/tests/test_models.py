"""User app tests."""

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


@pytest.mark.django_db
class TestUserRegistration:
    """Test user registration."""

    def setup_method(self):
        settings.API_KEYS = ["test-api-key"]

    def test_register_user(self):
        """Test creating a new user."""
        client = APIClient()
        client.credentials(HTTP_X_API_KEY="test-api-key")
        data = {
            "username": "testuser",
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
        }
        response = client.post("/api/v1/user/", data)
        assert response.status_code == 201
        assert User.objects.count() == 1

    def test_duplicate_username(self):
        """Test that duplicate usernames are rejected."""
        User.objects.create_user(username="testuser", email="test1@example.com")
        client = APIClient()
        client.credentials(HTTP_X_API_KEY="test-api-key")
        data = {
            "username": "testuser",
            "email": "test2@example.com",
        }
        response = client.post("/api/v1/user/", data)
        assert response.status_code == 400
