"""Vacancy serializers."""

from rest_framework import serializers

from apps.vacancies.models import Vacancy


class VacancyListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for vacancy list view."""

    class Meta:
        model = Vacancy
        fields = [
            "id",
            "title",
            "company",
            "salary_min",
            "salary_max",
            "salary_currency",
            "employment_type",
            "work_format",
            "location",
            "country",
            "region",
            "skills",
            "language",
            "source_channel",
            "source_message_id",
            "source_url",
            "posted_at",
            "created_at",
        ]


class VacancyDetailSerializer(serializers.ModelSerializer):
    """Full serializer for vacancy detail view."""

    class Meta:
        model = Vacancy
        fields = [
            "id",
            "title",
            "company",
            "description",
            "salary_min",
            "salary_max",
            "salary_currency",
            "employment_type",
            "work_format",
            "location",
            "country",
            "region",
            "experience_years",
            "skills",
            "contact_info",
            "language",
            "source",
            "source_channel",
            "source_url",
            "posted_at",
            "created_at",
            "updated_at",
        ]
