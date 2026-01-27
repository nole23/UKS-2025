from django.db import models
from repository.models import Repository

# Create your models here.
class Tag(models.Model):
    name = models.CharField(max_length=100)
    digest = models.CharField(max_length=255, default="")
    os_arch = models.CharField(max_length=50, default="linux/amd64")

    compressed_size_mb = models.FloatField(default=0.0)  # 👈 OVO DODAJ

    repository = models.ForeignKey(
        Repository,
        on_delete=models.CASCADE,
        related_name="tags"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"{self.repository.name}:{self.name}"
