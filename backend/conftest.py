"""Pytest configuration and fixtures."""

import os

import django
import pytest

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

# Setup Django
django.setup()


@pytest.fixture
def api_client():
    """Fixture for API client."""
    from rest_framework.test import APIClient

    return APIClient()


@pytest.fixture
def authenticated_client(api_client):
    """Fixture for authenticated API client."""
    from django.contrib.auth import get_user_model

    user_model = get_user_model()
    user = user_model.objects.create_user(
        username="testuser", email="test@example.com", password="testpass123"
    )
    api_client.force_authenticate(user=user)
    return api_client, user


@pytest.fixture
def sample_user():
    """Fixture for a sample user."""
    from django.contrib.auth import get_user_model

    user = get_user_model()
    return user.objects.create_user(
        username="sampleuser", email="sample@example.com", password="samplepass123"
    )
