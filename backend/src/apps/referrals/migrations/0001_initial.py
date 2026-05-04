"""Referrals migrations."""

import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Referral",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("referral_code", models.CharField(db_index=True, max_length=20, unique=True)),
                ("total_referrals", models.IntegerField(default=0)),
                (
                    "total_commission",
                    models.DecimalField(decimal_places=2, default=0, max_digits=10),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="referral",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "referrals",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="ReferralSignup",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("referral_code", models.CharField(db_index=True, max_length=20)),
                ("signup_date", models.DateTimeField(auto_now_add=True)),
                (
                    "subscription_status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("active", "Active"),
                            ("cancelled", "Cancelled"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                (
                    "commission_earned",
                    models.DecimalField(decimal_places=2, default=0, max_digits=10),
                ),
                ("commission_paid", models.BooleanField(default=False)),
                ("paid_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "referrer",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="signups",
                        to="referrals.referral",
                    ),
                ),
                (
                    "referred_user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="referred_by",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "referral_signups",
                "ordering": ["-signup_date"],
            },
        ),
        migrations.AddIndex(
            model_name="referralsignup",
            index=models.Index(fields=["referral_code"], name="referral_s_referr_idx"),
        ),
        migrations.AddIndex(
            model_name="referralsignup",
            index=models.Index(fields=["referred_user"], name="referral_s_referr_user_idx"),
        ),
    ]
