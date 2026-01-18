from django.db import models
from repository.models import Repository

# Create your models here.
class Tag(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    # Repository → Tag (1 : *)
    repository = models.ForeignKey(
        Repository,
        on_delete=models.CASCADE,
        related_name="tags"
    )

    def __str__(self):
        return self.name
