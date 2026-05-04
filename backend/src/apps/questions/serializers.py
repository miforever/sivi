# apps/questions/serializers.py
"""Serializers for Question models."""

from rest_framework import serializers

from apps.questions.models import Question, QuestionTranslation


class QuestionTranslationSerializer(serializers.ModelSerializer):
    """Serializer for question translations."""

    class Meta:
        model = QuestionTranslation
        fields = ["language", "text"]


class QuestionSerializer(serializers.ModelSerializer):
    """Serializer for questions with translations."""

    translations = QuestionTranslationSerializer(many=True, read_only=True)
    text = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = [
            "id",
            "position",
            "category",
            "field_name",
            "is_required",
            "order",
            "question_type",
            "meta",
            "translations",
            "text",  # Single language text based on request
        ]

    def get_text(self, obj):
        """Get question text in requested language"""
        # Get language from context (set in view)
        language = self.context.get("language", "en")

        translation = obj.translations.filter(language=language).first()
        if translation:
            return translation.text

        # Fallback to English
        fallback = obj.translations.filter(language="en").first()
        return fallback.text if fallback else ""


class QuestionListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing questions."""

    text = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = ["id", "field_name", "is_required", "order", "text", "question_type", "category"]

    def get_text(self, obj):
        """Get question text in requested language"""
        language = self.context.get("language", "en")
        translation = obj.translations.filter(language=language).first()

        if translation:
            return translation.text

        fallback = obj.translations.filter(language="en").first()
        return fallback.text if fallback else ""
