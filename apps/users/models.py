from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):

    ROLE_ADMIN = "admin"
    ROLE_USER = "user"

    ROLE_CHOICES = (
        (ROLE_ADMIN, "Admin"),
        (ROLE_USER, "User"),
    )

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile"
    )

    phone = models.CharField(max_length=15)

    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default=ROLE_USER
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} ({self.role})"

    @property
    def is_admin(self):
        return self.role == self.ROLE_ADMIN

    @property
    def is_user(self):
        return self.role == self.ROLE_USER
