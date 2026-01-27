# repository/models.py
from django.db import models
from user.models import User
from Organization.models import Organization

class Repository(models.Model):
    VISIBILITY_CHOICES = (
        ("public", "Public"),
        ("private", "Private"),
    )

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES)

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="owned_repositories",
        null=True,
        blank=True
    )

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="repositories",
        null=True,
        blank=True
    )

    stars_count = models.PositiveIntegerField(default=0)
    pulls_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    last_pushed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name


class RepositoryCollaborator(models.Model):
    ROLE_CHOICES = (
        ("admin", "Admin"),
        ("write", "Write"),
        ("read", "Read"),
    )

    repository = models.ForeignKey(
        Repository,
        on_delete=models.CASCADE,
        related_name="collaborators"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="repository_roles"
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)

    class Meta:
        unique_together = ("repository", "user")

    def __str__(self):
        return f"{self.user} - {self.role} on {self.repository}"
