"""Matching app models."""

from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class VacancyImpression(models.Model):
    """Records when a vacancy was shown to a user in the job feed.

    Used to exclude already-seen vacancies from subsequent match requests,
    so the feed doesn't replay the same top matches across sessions.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="vacancy_impressions",
    )
    vacancy = models.ForeignKey(
        "vacancies.Vacancy",
        on_delete=models.CASCADE,
        related_name="impressions",
    )
    shown_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(
                fields=["user", "-shown_at"],
                name="matching_va_user_id_shown_idx",
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "vacancy"],
                name="unique_user_vacancy_impression",
            ),
        ]

    def __str__(self):
        return f"{self.user_id} saw {self.vacancy_id} at {self.shown_at}"
