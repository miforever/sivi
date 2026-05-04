"""Unit tests for matching service helpers."""

from datetime import timedelta
from unittest.mock import MagicMock

import pytest
from django.utils import timezone

from apps.matching.services.matcher import (
    _extract_hard_skills,
    _normalize_skill,
    _recency_boost,
    _skill_f1,
    _title_similarity,
    _tokenize_title,
)

# ---------------------------------------------------------------------------
# _skill_f1
# ---------------------------------------------------------------------------


class TestSkillF1:
    def test_empty_resume_skills(self):
        assert _skill_f1(set(), {"python"}) == 0.0

    def test_empty_vacancy_skills(self):
        assert _skill_f1({"python"}, set()) == 0.0

    def test_both_empty(self):
        assert _skill_f1(set(), set()) == 0.0

    def test_identical_sets(self):
        assert _skill_f1({"python", "django"}, {"python", "django"}) == 1.0

    def test_disjoint_sets(self):
        assert _skill_f1({"python"}, {"java"}) == 0.0

    def test_partial_overlap(self):
        # resume: {python, django, react, vue}, vacancy: {python, django}
        # precision = 2/4 = 0.5, recall = 2/2 = 1.0
        # f1 = 2 * 0.5 * 1.0 / (0.5 + 1.0) = 2/3
        result = _skill_f1({"python", "django", "react", "vue"}, {"python", "django"})
        assert abs(result - 2 / 3) < 1e-9

    def test_large_resume_does_not_trivially_max(self):
        """A resume with 20 skills should not score 1.0 against a 2-skill vacancy."""
        resume = {f"skill{i}" for i in range(20)}
        vacancy = {"skill0", "skill1"}
        score = _skill_f1(resume, vacancy)
        assert score < 0.5

    def test_symmetry_differs(self):
        """F1 is symmetric — swap should give the same result."""
        a = {"python", "django"}
        b = {"python", "java", "go"}
        assert _skill_f1(a, b) == _skill_f1(b, a)


# ---------------------------------------------------------------------------
# _title_similarity
# ---------------------------------------------------------------------------


class TestTitleSimilarity:
    def test_identical_titles(self):
        assert _title_similarity("Python Developer", "Python Developer") == 1.0

    def test_empty_resume_title(self):
        assert _title_similarity("", "Python Developer") == 0.0

    def test_empty_vacancy_title(self):
        assert _title_similarity("Python Developer", "") == 0.0

    def test_partial_match(self):
        score = _title_similarity("Senior Python Developer", "Python Developer")
        assert 0.0 < score < 1.0

    def test_no_overlap(self):
        assert _title_similarity("Frontend Designer", "Backend Engineer") == 0.0

    def test_case_insensitive(self):
        assert _title_similarity("python developer", "PYTHON DEVELOPER") == 1.0


# ---------------------------------------------------------------------------
# _tokenize_title
# ---------------------------------------------------------------------------


class TestTokenizeTitle:
    def test_basic(self):
        tokens = _tokenize_title("Senior Python Developer")
        assert "python" in tokens
        assert "developer" in tokens
        assert "senior" in tokens

    def test_special_chars(self):
        tokens = _tokenize_title("C++ / Go Engineer")
        assert "c++" in tokens
        assert "go" in tokens
        assert "engineer" in tokens

    def test_empty(self):
        assert _tokenize_title("") == set()

    def test_stopwords_excluded(self):
        tokens = _tokenize_title("Head of Engineering")
        assert "of" not in tokens

    def test_short_tokens_excluded(self):
        tokens = _tokenize_title("A Senior Engineer")
        assert "a" not in tokens


# ---------------------------------------------------------------------------
# _recency_boost
# ---------------------------------------------------------------------------


class TestRecencyBoost:
    def _make_vacancy(self, posted_at=None, created_at=None):
        v = MagicMock()
        v.posted_at = posted_at
        v.created_at = created_at
        return v

    def test_today_is_max(self):
        v = self._make_vacancy(posted_at=timezone.now())
        assert _recency_boost(v) == pytest.approx(1.0, abs=0.02)

    def test_60_days_ago_is_zero(self):
        v = self._make_vacancy(posted_at=timezone.now() - timedelta(days=60))
        assert _recency_boost(v) == pytest.approx(0.0, abs=0.02)

    def test_older_than_60_days_clamped_to_zero(self):
        v = self._make_vacancy(posted_at=timezone.now() - timedelta(days=90))
        assert _recency_boost(v) == 0.0

    def test_falls_back_to_created_at(self):
        v = self._make_vacancy(posted_at=None, created_at=timezone.now() - timedelta(days=30))
        score = _recency_boost(v)
        assert score == pytest.approx(0.5, abs=0.02)

    def test_no_dates_returns_zero(self):
        v = self._make_vacancy(posted_at=None, created_at=None)
        assert _recency_boost(v) == 0.0


# ---------------------------------------------------------------------------
# _normalize_skill / _extract_hard_skills (regression)
# ---------------------------------------------------------------------------


class TestNormalizeSkill:
    def test_alias_resolution(self):
        assert _normalize_skill("js") == "javascript"
        assert _normalize_skill("k8s") == "kubernetes"
        assert _normalize_skill("drf") == "django rest framework"

    def test_case_insensitive(self):
        assert _normalize_skill("Python") == "python"

    def test_trailing_dot_stripped(self):
        assert _normalize_skill("python.") == "python"

    def test_unknown_passthrough(self):
        assert _normalize_skill("fastapi") == "fastapi"


class TestExtractHardSkills:
    def test_soft_skills_excluded(self):
        skills = _extract_hard_skills(["Python", "communication", "teamwork"])
        assert "python" in skills
        assert "communication" not in skills
        assert "teamwork" not in skills

    def test_empty_input(self):
        assert _extract_hard_skills([]) == set()
