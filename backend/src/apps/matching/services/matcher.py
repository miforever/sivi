"""Matching service — hybrid resume-to-vacancy matching.

Blends pgvector cosine similarity with skill F1, title Jaccard, and a
recency boost. Missing signals collapse back into the semantic score so
the final match score stays on a 0–1 scale.
"""

import logging
import re

from django.db import connection, models, transaction
from django.utils import timezone
from pgvector.django import CosineDistance

from apps.resumes.models import Resume
from apps.vacancies.models import Vacancy

from .embedding import (
    get_embedding_service,
    prepare_resume_text,
    prepare_vacancy_text,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Skill normalisation helpers
# ---------------------------------------------------------------------------

_SKILL_ALIASES: dict[str, str] = {
    "js": "javascript",
    "ts": "typescript",
    "c#": "csharp",
    "c++": "cpp",
    "golang": "go",
    "postgres": "postgresql",
    "psql": "postgresql",
    "mongo": "mongodb",
    "react.js": "react",
    "reactjs": "react",
    "next.js": "nextjs",
    "node.js": "nodejs",
    "node": "nodejs",
    "vue.js": "vue",
    "vuejs": "vue",
    "express.js": "express",
    "expressjs": "express",
    "flask": "flask",
    "drf": "django rest framework",
    "django rest": "django rest framework",
    "ml": "machine learning",
    "dl": "deep learning",
    "ai": "artificial intelligence",
    "aws": "amazon web services",
    "gcp": "google cloud platform",
    "k8s": "kubernetes",
    "pg": "postgresql",
    "mysql": "mysql",
    "sql server": "mssql",
    "dotnet": ".net",
    "asp.net": ".net",
}

# Generic soft skills that don't help distinguish vacancies
_SOFT_SKILLS: set[str] = {
    "communication",
    "teamwork",
    "leadership",
    "problem solving",
    "problem-solving",
    "critical thinking",
    "time management",
    "creativity",
    "adaptability",
    "work ethic",
    "attention to detail",
    "interpersonal",
    "collaboration",
    "motivation",
    "flexibility",
    "organization",
    "multitasking",
    "decision making",
    "negotiation",
    "presentation",
    "public speaking",
    "conflict resolution",
    "emotional intelligence",
    "stress management",
    "self-motivation",
    "коммуникабельность",
    "ответственность",
    "пунктуальность",
    "стрессоустойчивость",
    "работа в команде",
    "обучаемость",
    "muloqot",
    "jamoaviy ish",
    "mas'uliyat",
}


def _normalize_skill(name: str) -> str:
    """Lowercase, strip, and resolve aliases."""
    s = name.lower().strip().rstrip(".")
    return _SKILL_ALIASES.get(s, s)


def _extract_hard_skills(names: list[str]) -> set[str]:
    """Return normalised hard skills, excluding soft skills."""
    result = set()
    for name in names:
        norm = _normalize_skill(name)
        if norm and norm not in _SOFT_SKILLS:
            result.add(norm)
    return result


def _skill_f1(resume_skills: set[str], vacancy_skills: set[str]) -> float:
    """F1-style skill score balancing coverage and precision.

    Using F1 (not raw overlap / vacancy_skills) stops resumes that list 50
    skills from trivially scoring 1.0 against 3-skill vacancies.
    """
    if not resume_skills or not vacancy_skills:
        return 0.0
    inter = len(resume_skills & vacancy_skills)
    if inter == 0:
        return 0.0
    precision = inter / len(resume_skills)
    recall = inter / len(vacancy_skills)
    return 2 * precision * recall / (precision + recall)


_TITLE_STOPWORDS: set[str] = {
    "the",
    "a",
    "an",
    "and",
    "or",
    "of",
    "for",
    "to",
    "in",
    "at",
    "with",
}

_TITLE_TOKEN_RE = re.compile(r"[a-zа-яё0-9\+\#]+", re.IGNORECASE)


def _tokenize_title(title: str) -> set[str]:
    if not title:
        return set()
    tokens = _TITLE_TOKEN_RE.findall(title.lower())
    return {t for t in tokens if len(t) > 1 and t not in _TITLE_STOPWORDS}


def _title_similarity(resume_title: str, vacancy_title: str) -> float:
    """Jaccard similarity of normalized title tokens."""
    r = _tokenize_title(resume_title or "")
    v = _tokenize_title(vacancy_title or "")
    if not r or not v:
        return 0.0
    return len(r & v) / len(r | v)


def _recency_boost(vacancy) -> float:
    """Linear decay over 60 days — fresher vacancies rank higher on ties."""
    ref = vacancy.posted_at or vacancy.created_at
    if ref is None:
        return 0.0
    age_days = (timezone.now() - ref).days
    return max(0.0, 1.0 - age_days / 60.0)


# ---------------------------------------------------------------------------
# Weights
# ---------------------------------------------------------------------------

_W_SEMANTIC = 0.40
_W_TITLE = 0.15
_W_SKILL = 0.35
_W_RECENCY = 0.10


class MatcherService:
    """Orchestrates hybrid resume-to-vacancy matching."""

    def __init__(self):
        self._embedding_service = None

    @property
    def embedding_service(self):
        if self._embedding_service is None:
            self._embedding_service = get_embedding_service()
        return self._embedding_service

    def generate_vacancy_embedding(self, vacancy: Vacancy) -> None:
        """Generate and store embedding for a single vacancy."""
        text = prepare_vacancy_text(vacancy)
        embeddings = self.embedding_service.embed([text])
        vacancy.embedding = embeddings[0]
        vacancy.save(update_fields=["embedding"])
        logger.debug("Generated embedding for vacancy %s", vacancy.id)

    def generate_vacancy_embeddings_batch(self, vacancies: list[Vacancy]) -> int:
        """Generate embeddings for a batch of vacancies. Returns count of updated."""
        if not vacancies:
            return 0

        texts = [prepare_vacancy_text(v) for v in vacancies]
        embeddings = self.embedding_service.embed(texts)

        for vacancy, embedding in zip(vacancies, embeddings):
            vacancy.embedding = embedding

        Vacancy.objects.bulk_update(vacancies, ["embedding"])
        logger.info("Generated embeddings for %d vacancies", len(vacancies))
        return len(vacancies)

    def find_matching_vacancies(
        self,
        resume: Resume,
        limit: int = 20,
        filters: dict | None = None,
        exclude_ids: list | None = None,
    ):
        """Find top-N vacancies matching a resume.

        Blended scoring:
          final = 0.55*semantic + 0.15*title + 0.20*skill_f1 + 0.10*recency
        Unavailable components have their weight redistributed onto the
        semantic score so results stay on a 0–1 scale.

        Returns a list of Vacancy objects annotated with ``distance``,
        ``match_score``, and ``skill_score`` (0–1, higher = better).
        """
        if resume.embedding is not None:
            resume_embedding = resume.embedding
        else:
            resume_text = prepare_resume_text(resume)
            resume_embedding = self.embedding_service.embed([resume_text])[0]
            resume.embedding = resume_embedding
            resume.save(update_fields=["embedding"])

        qs = Vacancy.objects.exclude(embedding=None)

        if exclude_ids:
            qs = qs.exclude(id__in=exclude_ids)

        if filters:
            if filters.get("location"):
                qs = qs.filter(location__icontains=filters["location"])
            if filters.get("employment_type"):
                qs = qs.filter(employment_type=filters["employment_type"])
            if filters.get("work_format"):
                qs = qs.filter(work_format=filters["work_format"])
            if filters.get("language"):
                qs = qs.filter(language=filters["language"])
            if filters.get("salary_min"):
                qs = qs.filter(
                    models.Q(salary_max__gte=filters["salary_min"])
                    | models.Q(salary_max__isnull=True)
                )
            if filters.get("regions"):
                # Remote vacancies and untagged (legacy, region="") always visible
                qs = qs.filter(
                    models.Q(region__in=filters["regions"])
                    | models.Q(work_format="remote")
                    | models.Q(region="")
                )

        # --- Extract resume hard skills ---
        resume_skill_names = list(resume.skills.values_list("name", flat=True))
        resume_hard = _extract_hard_skills(resume_skill_names)
        resume_title = getattr(resume, "position", "") or ""

        # Wide rerank window: blended scoring can meaningfully reorder the
        # semantic top-N, so we need real breathing room beyond `limit`.
        fetch_limit = max(limit * 10, 100)

        # HNSW index returns approximate top-k where k is capped by
        # hnsw.ef_search (default 40). With filters like exclude_ids, the
        # filter can remove most/all of the approximate top-k, starving the
        # candidate pool. Raise ef_search enough to survive exclusions.
        ef_search = int(max(fetch_limit * 4, len(exclude_ids or []) * 2, 500))

        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(f"SET LOCAL hnsw.ef_search = {ef_search}")
            candidates = list(
                qs.annotate(distance=CosineDistance("embedding", resume_embedding)).order_by(
                    "distance"
                )[:fetch_limit]
            )

        for v in candidates:
            semantic = max(0.0, 1 - v.distance)

            # Skill F1 (if both sides have skills)
            vacancy_hard: set[str] = set()
            if v.skills:
                v_skills = []
                for s in v.skills:
                    if isinstance(s, dict) and "name" in s:
                        v_skills.append(s["name"])
                    elif isinstance(s, str):
                        v_skills.append(s)
                vacancy_hard = _extract_hard_skills(v_skills)

            has_skills = bool(resume_hard) and bool(vacancy_hard)
            skill_score = _skill_f1(resume_hard, vacancy_hard) if has_skills else 0.0

            # Title Jaccard (if both sides have a title)
            has_title = bool(resume_title) and bool(v.title)
            title_score = _title_similarity(resume_title, v.title) if has_title else 0.0

            recency = _recency_boost(v)
            has_recency = recency > 0.0 or (v.posted_at is not None or v.created_at is not None)

            # Redistribute weights of missing components onto semantic so the
            # final stays comparable across heterogeneous data.
            w_sem = _W_SEMANTIC
            w_title = _W_TITLE if has_title else 0.0
            w_skill = _W_SKILL if has_skills else 0.0
            w_rec = _W_RECENCY if has_recency else 0.0
            w_sem += (_W_TITLE - w_title) + (_W_SKILL - w_skill) + (_W_RECENCY - w_rec)

            v.match_score = round(
                w_sem * semantic + w_title * title_score + w_skill * skill_score + w_rec * recency,
                4,
            )
            v.skill_score = round(skill_score, 4)
            v.title_score = round(title_score, 4)
            v.recency_score = round(recency, 4)

        candidates.sort(key=lambda c: c.match_score, reverse=True)

        # Light diversity pass — cap each company at 2 in the final list.
        diversified: list = []
        per_company: dict[str, int] = {}
        for v in candidates:
            key = (v.company or "").strip().lower()
            if key:
                if per_company.get(key, 0) >= 2:
                    continue
                per_company[key] = per_company.get(key, 0) + 1
            diversified.append(v)
            if len(diversified) >= limit:
                break

        # Backfill with any remaining candidates if diversity trimmed too
        # aggressively (e.g. pool genuinely dominated by one company).
        if len(diversified) < limit:
            chosen = {id(v) for v in diversified}
            for v in candidates:
                if id(v) in chosen:
                    continue
                diversified.append(v)
                if len(diversified) >= limit:
                    break

        return diversified[:limit]
