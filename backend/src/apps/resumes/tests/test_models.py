"""Resume app tests."""

import pytest
from django.contrib.auth import get_user_model

from apps.resumes.models import Resume

User = get_user_model()


@pytest.mark.django_db
class TestResumeModel:
    """Test Resume model."""

    def test_create_resume(self):
        """Test creating a resume with current fields."""
        user = User.objects.create_user(username="testuser", email="test@example.com")
        resume = Resume.objects.create(
            user=user,
            title="Backend Developer Resume",
            full_name="Test User",
            position="Backend Developer",
            origin="qa_generated",
        )
        assert resume.title == "Backend Developer Resume"
        assert resume.user == user
        assert resume.origin == "qa_generated"
        assert resume.id is not None

    def test_resume_ordering(self):
        """Test that resumes are ordered by created_at descending."""
        user = User.objects.create_user(username="testuser2", email="test2@example.com")
        r1 = Resume.objects.create(user=user, title="First")
        r2 = Resume.objects.create(user=user, title="Second")
        resumes = list(Resume.objects.filter(user=user))
        assert resumes[0].id == r2.id
        assert resumes[1].id == r1.id
