"""User serializers."""

from rest_framework import serializers

from apps.common.regions import REGION_SLUGS
from apps.users.models import User


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""

    class Meta:
        model = User
        fields = [
            "id",
            "telegram_id",
            "username",
            "first_name",
            "last_name",
            "user_name",
            "phone",
            "language",
            "resume_credits",
            "preferred_regions",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating users."""

    class Meta:
        model = User
        fields = [
            "telegram_id",
            "username",
            "first_name",
            "last_name",
            "user_name",
            "phone",
            "language",
        ]

    def validate_telegram_id(self, value):
        """Validate telegram_id uniqueness."""
        if (
            value
            and User.objects.filter(telegram_id=value)
            .exclude(id=self.instance.id if self.instance else None)
            .exists()
        ):
            raise serializers.ValidationError("A user with this Telegram ID already exists.")
        return value


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating users (no telegram_id in body)."""

    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "user_name",
            "phone",
            "language",
            "preferred_regions",
        ]

    def validate_preferred_regions(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("Must be a list of region slugs.")
        invalid = [s for s in value if s not in REGION_SLUGS]
        if invalid:
            raise serializers.ValidationError(f"Invalid region slugs: {invalid}")
        return value
