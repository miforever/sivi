from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("matching", "0001_enable_pgvector"),
        ("vacancies", "0004_rehash_content_hash"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="VacancyImpression",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("shown_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name="vacancy_impressions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "vacancy",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name="impressions",
                        to="vacancies.vacancy",
                    ),
                ),
            ],
            options={
                "indexes": [
                    models.Index(
                        fields=["user", "-shown_at"],
                        name="matching_va_user_id_shown_idx",
                    ),
                ],
                "constraints": [
                    models.UniqueConstraint(
                        fields=["user", "vacancy"],
                        name="unique_user_vacancy_impression",
                    ),
                ],
            },
        ),
    ]
