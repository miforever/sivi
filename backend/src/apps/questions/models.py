"""Question models."""

from django.db import models

from apps.common.constants import LANG_CHOICES, LANG_EN


class Question(models.Model):
    """
    Question model for interview/form questions.
    """

    QUESTION_TYPE_CHOICES = [
        ("text", "Text"),
        ("multi", "Multiple Choice"),
        ("file", "File Upload"),
    ]

    CATEGORY_CHOICES = [
        ("personal", "Personal Information"),
        ("professional", "Professional"),
        ("education", "Education"),
        ("skills", "Skills"),
        ("position_specific", "Position Specific"),
        ("other", "Other"),
    ]

    position = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Job position this question is for (null for generic questions)",
    )
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        default="professional",
        help_text="Question category",
    )
    field_name = models.CharField(
        max_length=100,
        help_text="Field name for mapping to resume data (e.g., 'experience', 'skills')",
    )
    is_required = models.BooleanField(
        default=True, help_text="Whether this question must be answered"
    )
    order = models.IntegerField(default=0, help_text="Display order within position/category")
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPE_CHOICES, default="text")
    meta = models.JSONField(
        default=dict, blank=True, help_text="Additional metadata (e.g., options for multi-choice)"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "questions"
        indexes = [
            models.Index(fields=["position", "category"]),
            models.Index(fields=["category"]),
            models.Index(fields=["order"]),
        ]
        ordering = ["order", "position", "category"]
        unique_together = [["position", "field_name", "order"]]

    def __str__(self):
        pos = self.position or "Generic"
        return f"{pos} - {self.category} - Order {self.order}"


class QuestionTranslation(models.Model):
    """
    Translations for questions to support multiple languages.
    """

    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="translations")
    language = models.CharField(max_length=10, choices=LANG_CHOICES, default=LANG_EN)
    text = models.TextField(help_text="Question text in this language")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "question_translations"
        unique_together = [["question", "language"]]
        indexes = [
            models.Index(fields=["question", "language"]),
            models.Index(fields=["language"]),
        ]

    def __str__(self):
        return f"{self.question.field_name} ({self.language})"
