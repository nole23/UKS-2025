from django.db import models
from user.models import User
from repository.models import Repository

# Create your models here.
class Star(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="stars"
    )
    repository = models.ForeignKey(
        Repository,
        on_delete=models.CASCADE,
        related_name="stars"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "repository")

    def __str__(self):
        return f"{self.user} starred {self.repository}"
