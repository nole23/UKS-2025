from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Repository
from star.models import Star
from pull.models import Pull

# Stars count
@receiver([post_save, post_delete], sender=Star)
def update_stars_count(sender, instance, **kwargs):
    repo = instance.repository
    repo.stars_count = repo.stars.count()
    repo.save(update_fields=['stars_count'])

# Pulls count
@receiver(post_save, sender=Pull)
def update_pulls_count(sender, instance, **kwargs):
    repo = instance.repository
    repo.pulls_count = repo.pulls.count()
    repo.save(update_fields=['pulls_count'])