"""Question app tests."""

import pytest
from rest_framework.test import APIClient

from apps.questions.models import Question, QuestionTranslation


@pytest.mark.django_db
class TestQuestionAPI:
    """Test question API endpoints."""

    def test_list_questions(self):
        """Test listing questions."""
        q = Question.objects.create(
            position=None,
            category="professional",
            field_name="experience",
            order=1,
        )
        QuestionTranslation.objects.create(
            question=q, language="en", text="What is your experience with Django?"
        )
        client = APIClient()
        response = client.get("/api/v1/questions/")
        assert response.status_code == 200
        assert response.data["success"] is True
        assert len(response.data["data"]) == 1

    def test_filter_by_position(self):
        """Test filtering questions by position."""
        generic = Question.objects.create(
            position=None, category="professional", field_name="summary", order=1
        )
        specific = Question.objects.create(
            position="Backend", category="professional", field_name="stack", order=2
        )
        QuestionTranslation.objects.create(
            question=generic, language="en", text="Tell me about yourself"
        )
        QuestionTranslation.objects.create(
            question=specific, language="en", text="What backend stack do you use?"
        )

        client = APIClient()
        response = client.get("/api/v1/questions/?position=Backend")
        assert response.status_code == 200
        # Should return both generic (position=None) and Backend-specific
        assert len(response.data["data"]) == 2

    def test_list_only_generic_without_position(self):
        """Without position param, only generic questions are returned."""
        generic = Question.objects.create(
            position=None, category="personal", field_name="name", order=1
        )
        specific = Question.objects.create(
            position="Frontend", category="professional", field_name="framework", order=1
        )
        QuestionTranslation.objects.create(
            question=generic, language="en", text="What is your name?"
        )
        QuestionTranslation.objects.create(
            question=specific, language="en", text="Which framework do you prefer?"
        )

        client = APIClient()
        response = client.get("/api/v1/questions/")
        assert response.status_code == 200
        assert len(response.data["data"]) == 1
        assert response.data["data"][0]["field_name"] == "name"
