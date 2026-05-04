from django.db import migrations, models


def uz2_to_cyr(apps, schema_editor):
    User = apps.get_model("users", "User")
    User.objects.filter(language="uz2").update(language="cyr")


def cyr_to_uz2(apps, schema_editor):
    User = apps.get_model("users", "User")
    User.objects.filter(language="cyr").update(language="uz2")


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0006_weekly_ai_limit"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="language",
            field=models.CharField(
                choices=[
                    ("en", "English"),
                    ("ru", "Russian"),
                    ("uz", "Uzbek"),
                    ("cyr", "Ozbek"),
                ],
                default="uz",
                help_text="User interface language preference",
                max_length=5,
            ),
        ),
        migrations.RunPython(uz2_to_cyr, cyr_to_uz2),
    ]
