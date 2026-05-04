import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()


class Command(BaseCommand):
    help = "Create or update the admin superuser from ADMIN_USERNAME / ADMIN_PASSWORD env vars."

    def handle(self, *args, **options):
        username = os.environ.get("ADMIN_USERNAME")
        password = os.environ.get("ADMIN_PASSWORD")

        if not username or not password:
            self.stderr.write("ADMIN_USERNAME and ADMIN_PASSWORD must be set in the environment.")
            return

        user, created = User.objects.get_or_create(username=username)
        user.set_password(password)
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.save()

        action = "Created" if created else "Updated"
        self.stdout.write(self.style.SUCCESS(f"{action} admin user: {username}"))

        # Ensure all superusers have is_staff (fixes pre-existing accounts)
        fixed = User.objects.filter(is_superuser=True, is_staff=False).update(is_staff=True)
        if fixed:
            self.stdout.write(
                self.style.SUCCESS(f"Also granted is_staff to {fixed} existing superuser(s)")
            )
