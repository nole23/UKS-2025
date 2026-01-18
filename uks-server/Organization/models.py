from django.db import models
from user.models import User

# Create your models here.
class Organization(models.Model):
    name = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # optional: owner (nije striktno u UML, ali je realno)
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="organizations"
    )

    def __str__(self):
        return self.name
