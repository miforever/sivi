"""Re-compute content_hash to include source_url for more precise dedup."""

import hashlib

from django.db import migrations


def rehash_vacancies(apps, schema_editor):
    Vacancy = apps.get_model("vacancies", "Vacancy")
    batch = []
    for v in Vacancy.objects.all().only("id", "source_url", "title", "company", "description"):
        raw = (
            f"{(v.source_url or '').strip()}"
            f"|{v.title.lower().strip()}"
            f"|{v.company.lower().strip()}"
            f"|{v.description[:500].lower().strip()}"
        )
        v.content_hash = hashlib.sha256(raw.encode()).hexdigest()
        batch.append(v)
        if len(batch) >= 1000:
            Vacancy.objects.bulk_update(batch, ["content_hash"])
            batch = []
    if batch:
        Vacancy.objects.bulk_update(batch, ["content_hash"])


class Migration(migrations.Migration):
    dependencies = [
        ("vacancies", "0003_add_country_field"),
    ]

    operations = [
        migrations.RunPython(rehash_vacancies, migrations.RunPython.noop),
    ]
