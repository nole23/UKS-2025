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
    created_at = models.DateTimeField(auto_now_add=True)

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="repositories",
        null=True,      # dozvoljava NULL
        blank=True      # dozvoljava prazno u admin i formama
    )

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="repositories",
        null=True,      # dozvoljava NULL
        blank=True      # dozvoljava prazno u admin i formama
    )

    def __str__(self):
        return f"{self.name} ({self.visibility})"
