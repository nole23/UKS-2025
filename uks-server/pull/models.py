from django.db import models
from user.models import User
from repository.models import Repository

# Create your models here.
class Pull(models.Model):
    repository = models.ForeignKey(
        Repository,
        on_delete=models.CASCADE,
        related_name="pulls"
    )
    pulled_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Pull on {self.repository.name}"
