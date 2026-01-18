from django.db import models
from user.models import User
from Organization.models import Organization

# Create your models here.
class Repository(models.Model):
    VISIBILITY_CHOICES = (
        ("public", "Public"),
        ("private", "Private"),
    )

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    # owns: User → Repository (1 : *)
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="repositories"
    )

    # contains: Organization → Repository (1 : *)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="repositories"
    )

    def __str__(self):
        return f"{self.name} ({self.visibility})"
