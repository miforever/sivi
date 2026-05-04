"""Vacancy and scrape state models."""

import uuid

from django.db import models
from pgvector.django import HnswIndex, VectorField


class VacancySource(models.TextChoices):
    TELEGRAM = "telegram", "Telegram"
    MANUAL = "manual", "Manual"
    API = "api", "API"


class EmploymentType(models.TextChoices):
    FULL_TIME = "full_time", "Full Time"
    PART_TIME = "part_time", "Part Time"
    CONTRACT = "contract", "Contract"
    INTERNSHIP = "internship", "Internship"
    FREELANCE = "freelance", "Freelance"


class WorkFormat(models.TextChoices):
    OFFICE = "office", "Office"
    REMOTE = "remote", "Remote"
    HYBRID = "hybrid", "Hybrid"


class Vacancy(models.Model):
    """Job vacancy aggregated from multiple sources."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Core fields
    title = models.CharField(max_length=500)
    company = models.CharField(max_length=255, blank=True, default="")
    description = models.TextField()

    # Structured fields
    salary_min = models.PositiveIntegerField(null=True, blank=True)
    salary_max = models.PositiveIntegerField(null=True, blank=True)
    salary_currency = models.CharField(max_length=10, blank=True, default="")
    employment_type = models.CharField(
        max_length=20, choices=EmploymentType.choices, blank=True, default=""
    )
    work_format = models.CharField(
        max_length=20, choices=WorkFormat.choices, blank=True, default=""
    )
    location = models.CharField(max_length=255, blank=True, default="")
    country = models.CharField(max_length=2, blank=True, default="UZ", db_index=True)
    region = models.CharField(max_length=30, blank=True, default="", db_index=True)
    experience_years = models.PositiveSmallIntegerField(null=True, blank=True)
    skills = models.JSONField(default=list, blank=True)
    contact_info = models.CharField(max_length=500, blank=True, default="")
    language = models.CharField(max_length=10, blank=True, default="")

    # Source tracking
    source = models.CharField(
        max_length=20, choices=VacancySource.choices, default=VacancySource.TELEGRAM
    )
    source_channel = models.CharField(max_length=100, blank=True, default="")
    source_message_id = models.PositiveIntegerField(null=True, blank=True)
    source_url = models.URLField(max_length=500, blank=True, default="")
    posted_at = models.DateTimeField(null=True, blank=True)

    # Raw data preservation
    raw_data = models.JSONField(default=dict, blank=True)

    # Semantic search embedding (BGE-M3, 1024 dimensions)
    embedding = VectorField(dimensions=1024, null=True, blank=True)

    # Deduplication
    content_hash = models.CharField(max_length=64, unique=True, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "vacancies"
        indexes = [
            models.Index(fields=["company"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["source_channel"]),
            models.Index(fields=["posted_at"]),
            HnswIndex(
                name="vacancy_embedding_hnsw_idx",
                fields=["embedding"],
                m=16,
                ef_construction=64,
                opclasses=["vector_cosine_ops"],
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["source_channel", "source_message_id"],
                name="unique_channel_message",
            ),
        ]
        ordering = ["-posted_at", "-created_at"]

    def __str__(self):
        return f"{self.title} at {self.company}" if self.company else self.title


class ScrapeState(models.Model):
    """Track last scraped message ID per channel for incremental fetching."""

    channel_username = models.CharField(max_length=100, unique=True)
    last_message_id = models.PositiveIntegerField(default=0)
    last_scraped_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "scrape_state"

    def __str__(self):
        return f"@{self.channel_username} (last: {self.last_message_id})"
