from django.db import migrations, models


def uz2_to_cyr(apps, schema_editor):
    QuestionTranslation = apps.get_model("questions", "QuestionTranslation")
    QuestionTranslation.objects.filter(language="uz2").update(language="cyr")


def cyr_to_uz2(apps, schema_editor):
    QuestionTranslation = apps.get_model("questions", "QuestionTranslation")
    QuestionTranslation.objects.filter(language="cyr").update(language="uz2")


class Migration(migrations.Migration):
    dependencies = [
        ("questions", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="questiontranslation",
            name="language",
            field=models.CharField(
                choices=[
                    ("en", "English"),
                    ("ru", "Russian"),
                    ("uz", "Uzbek"),
                    ("cyr", "Ozbek"),
                ],
                default="en",
                max_length=10,
            ),
        ),
        migrations.RunPython(uz2_to_cyr, cyr_to_uz2),
    ]
