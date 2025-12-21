from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.users.models import UserProfile

class Command(BaseCommand):
    help = "Create initial super admin user"

    def handle(self, *args, **kwargs):
        username = "admin"
        password = "Admin@123"
        email = "admin@test.com"
        first_name = "Super"
        last_name = "Admin"
        phone = "9999999999"

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING("Superadmin already exists"))
            return

        user = User.objects.create_superuser(
            username=username,
            password=password,
            email=email,
            first_name=first_name,
            last_name=last_name
        )

        UserProfile.objects.create(
            user=user,
            phone=phone,
            role="admin"
        )

        self.stdout.write(self.style.SUCCESS("Superadmin created successfully"))
