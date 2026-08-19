from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand, CommandError

from app.utils.docs_auth import DOCS_GROUP


class Command(BaseCommand):
    help = (
        "Create or update a user who may read the API documentation. "
        "The account is non-staff: it cannot log into the admin."
    )

    def add_arguments(self, parser):
        parser.add_argument("username")
        parser.add_argument("--password", required=True)

    def handle(self, *args, **options):
        username = options["username"]
        password = options["password"]

        user, created = User.objects.get_or_create(username=username)
        if user.is_staff or user.is_superuser:
            raise CommandError(
                f"'{username}' is an admin account. Use a separate, non-admin "
                "username for documentation access."
            )

        user.set_password(password)
        user.is_active = True
        user.is_staff = False
        user.save()

        group, _ = Group.objects.get_or_create(name=DOCS_GROUP)
        user.groups.add(group)

        action = "Created" if created else "Updated"
        self.stdout.write(self.style.SUCCESS(
            f"{action} docs user '{username}' (group: {DOCS_GROUP}, staff: no)."
        ))
