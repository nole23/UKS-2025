from django.contrib.auth.models import Permission
from django.db import models

class User(models.Model):
    """
    Extends Django built-in user.
    """
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)

    # permissions: User ↔ Permission (many-to-many)
    user_permissions = models.ManyToManyField(
        Permission,
        blank=True,
        related_name="dockerhub_users"
    )

    def __str__(self):
        return self.username
