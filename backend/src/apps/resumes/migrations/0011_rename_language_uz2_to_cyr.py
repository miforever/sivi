from django.db import migrations


def uz2_to_cyr(apps, schema_editor):
    Resume = apps.get_model("resumes", "Resume")
    Resume.objects.filter(language="uz2").update(language="cyr")


def cyr_to_uz2(apps, schema_editor):
    Resume = apps.get_model("resumes", "Resume")
    Resume.objects.filter(language="cyr").update(language="uz2")


class Migration(migrations.Migration):
    dependencies = [
        ("resumes", "0010_add_resume_embedding"),
    ]

    operations = [
        migrations.RunPython(uz2_to_cyr, cyr_to_uz2),
    ]
