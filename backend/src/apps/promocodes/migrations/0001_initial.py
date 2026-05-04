# Generated migration for promocodes models

import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        (
            "subscriptions",
            "0002_rename_subscripti_user_id_status_idx_subscriptio_user_id_8d58fd_idx_and_more",
        ),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Promocode",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("code", models.CharField(db_index=True, max_length=50, unique=True)),
                ("description", models.TextField(blank=True, default="")),
                (
                    "discount_percent",
                    models.IntegerField(default=0, help_text="Discount percentage (0-100)"),
                ),
                (
                    "discount_amount",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        help_text="Fixed discount amount",
                        max_digits=10,
                        null=True,
                    ),
                ),
                (
                    "max_uses",
                    models.IntegerField(default=0, help_text="Maximum uses (0 = unlimited)"),
                ),
                ("used_count", models.IntegerField(default=0)),
                (
                    "applicable_plans",
                    models.JSONField(
                        default=list,
                        help_text="List of plan IDs this code applies to (empty = all)",
                    ),
                ),
                ("valid_from", models.DateTimeField(blank=True, null=True)),
                ("valid_until", models.DateTimeField(blank=True, null=True)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "promocodes",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="PromoCodeUsage",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("code", models.CharField(db_index=True, max_length=50)),
                (
                    "discount_applied",
                    models.DecimalField(decimal_places=2, default=0, max_digits=10),
                ),
                ("used_at", models.DateTimeField(auto_now_add=True)),
                (
                    "promocode",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="promocodes.promocode",
                    ),
                ),
                (
                    "subscription",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="promocode_usages",
                        to="subscriptions.subscription",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="promocode_usages",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "promocode_usages",
                "ordering": ["-used_at"],
            },
        ),
        migrations.AddIndex(
            model_name="promocode",
            index=models.Index(fields=["code"], name="promocodes_code_idx"),
        ),
        migrations.AddIndex(
            model_name="promocode",
            index=models.Index(fields=["is_active"], name="promocodes_is_active_idx"),
        ),
        migrations.AddIndex(
            model_name="promocodeusage",
            index=models.Index(fields=["user", "code"], name="promocode_u_user_id_code_idx"),
        ),
        migrations.AddIndex(
            model_name="promocodeusage",
            index=models.Index(fields=["code"], name="promocode_u_code_idx"),
        ),
    ]
