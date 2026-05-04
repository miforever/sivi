"""Embedding service — provider-agnostic interface + Fireworks BGE-M3 implementation."""

import abc
import logging
import time

from django.conf import settings

logger = logging.getLogger(__name__)


def _log_api_call(
    *,
    provider: str,
    endpoint: str,
    tokens_used: int,
    cost: float,
    response_time_ms: int,
    success: bool,
    error_message: str = "",
) -> None:
    """Best-effort write to APICallLog — never raises."""
    try:
        from apps.analytics.models import APICallLog

        APICallLog.objects.create(
            provider=provider,
            endpoint=endpoint,
            tokens_used=tokens_used,
            cost=cost,
            response_time_ms=response_time_ms,
            success=success,
            error_message=error_message,
        )
    except Exception:
        logger.debug("Failed to log API call", exc_info=True)


class EmbeddingService(abc.ABC):
    """Abstract embedding provider."""

    @abc.abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a batch of texts.

        Returns list of vectors, one per input text.
        """
        ...


class FireworksEmbeddingService(EmbeddingService):
    """BGE-M3 embeddings via Fireworks.ai OpenAI-compatible API."""

    BASE_URL = "https://api.fireworks.ai/inference/v1"

    def __init__(self):
        self.api_key = settings.FIREWORKS_API_KEY
        self.model = settings.FIREWORKS_EMBEDDING_MODEL
        self.dimensions = settings.EMBEDDING_DIMENSIONS
        if not self.api_key:
            raise ValueError("FIREWORKS_API_KEY not configured")

    def embed(self, texts: list[str]) -> list[list[float]]:
        from openai import OpenAI

        client = OpenAI(api_key=self.api_key, base_url=self.BASE_URL)
        t0 = time.time()
        try:
            response = client.embeddings.create(
                model=self.model,
                input=texts,
            )
            elapsed_ms = int((time.time() - t0) * 1000)
            tokens = getattr(getattr(response, "usage", None), "total_tokens", len(texts))
            _log_api_call(
                provider="fireworks",
                endpoint=self.model,
                tokens_used=tokens,
                cost=0,
                response_time_ms=elapsed_ms,
                success=True,
            )
        except Exception as e:
            elapsed_ms = int((time.time() - t0) * 1000)
            _log_api_call(
                provider="fireworks",
                endpoint=self.model,
                tokens_used=0,
                cost=0,
                response_time_ms=elapsed_ms,
                success=False,
                error_message=str(e),
            )
            raise
        # Sort by index to preserve input order
        sorted_data = sorted(response.data, key=lambda x: x.index)
        return [item.embedding for item in sorted_data]


def get_embedding_service() -> EmbeddingService:
    """Factory: returns the configured embedding service."""
    return FireworksEmbeddingService()


def prepare_vacancy_text(vacancy) -> str:
    """Build the text to embed for a vacancy.

    Combines title + skills + description for maximum semantic signal.
    """
    parts = [vacancy.title]
    if vacancy.skills:
        parts.append(", ".join(vacancy.skills))
    if vacancy.description:
        parts.append(vacancy.description[:2000])
    return "\n".join(parts)


def prepare_resume_text(resume) -> str:
    """Build the text to embed for a resume.

    Combines position + summary + skills + experience for cross-lingual matching.
    """
    parts = []
    if resume.position:
        parts.append(resume.position)
    if resume.professional_summary:
        parts.append(resume.professional_summary)

    skill_names = list(resume.skills.values_list("name", flat=True))
    if skill_names:
        parts.append(", ".join(skill_names))

    for exp in resume.experiences.all()[:5]:
        exp_text = f"{exp.position} at {exp.company}"
        if exp.responsibilities:
            exp_text += ". " + ". ".join(exp.responsibilities[:3])
        parts.append(exp_text)

    return "\n".join(parts)
