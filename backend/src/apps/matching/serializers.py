"""Matching serializers."""

from rest_framework import serializers

from apps.vacancies.serializers import VacancyListSerializer


class MatchRequestSerializer(serializers.Serializer):
    resume_id = serializers.UUIDField()
    limit = serializers.IntegerField(default=20, min_value=1, max_value=50)
    filters = serializers.DictField(required=False, default=dict)
    exclude_ids = serializers.ListField(child=serializers.UUIDField(), required=False, default=list)


class MatchedVacancySerializer(VacancyListSerializer):
    """Vacancy with hybrid match score (semantic + skill overlap)."""

    similarity_score = serializers.SerializerMethodField()
    skill_score = serializers.SerializerMethodField()

    class Meta(VacancyListSerializer.Meta):
        fields = [*VacancyListSerializer.Meta.fields, "similarity_score", "skill_score"]

    def get_similarity_score(self, obj):
        if hasattr(obj, "match_score"):
            return obj.match_score
        if hasattr(obj, "distance"):
            return round(1 - obj.distance, 4)
        return None

    def get_skill_score(self, obj):
        return getattr(obj, "skill_score", 0.0)
