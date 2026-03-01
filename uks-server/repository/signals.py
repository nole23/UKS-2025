from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from star.models import Star
from pull.models import Pull
from utils.logger import UKSLogger, UKSAuditLogger

# Stars count
@receiver([post_save, post_delete], sender=Star)
def update_stars_count(sender, instance, **kwargs):
    repo = instance.repository
    UKSLogger.debug(f"update_stars_count started for repo_id={repo.id}")
    try:
        old_count = repo.stars_count
        repo.stars_count = repo.stars.count()
        repo.save(update_fields=['stars_count'])
        UKSLogger.info(f"Stars count updated for repo_id={repo.id}: {old_count} -> {repo.stars_count}")
        UKSAuditLogger.info(f"STARS_COUNT_UPDATED | repo_id={repo.id} | old={old_count} | new={repo.stars_count} | user_id={instance.user.id}")
    except Exception as ex:
        UKSLogger.error(f"Failed to update stars count for repo_id={repo.id}: {ex}")
        UKSAuditLogger.info(f"STARS_COUNT_UPDATE_FAILED | repo_id={repo.id} | error={ex}")
    finally:
        UKSLogger.debug(f"update_stars_count ended for repo_id={repo.id}")


# Pulls count
@receiver(post_save, sender=Pull)
def update_pulls_count(sender, instance, **kwargs):
    repo = instance.repository
    UKSLogger.debug(f"update_pulls_count started for repo_id={repo.id}")
    try:
        old_count = repo.pulls_count
        repo.pulls_count = repo.pulls.count()
        repo.save(update_fields=['pulls_count'])
        UKSLogger.info(f"Pulls count updated for repo_id={repo.id}: {old_count} -> {repo.pulls_count}")
        UKSAuditLogger.info(f"PULLS_COUNT_UPDATED | repo_id={repo.id} | old={old_count} | new={repo.pulls_count} | user_id={instance.user.id}")
    except Exception as ex:
        UKSLogger.error(f"Failed to update pulls count for repo_id={repo.id}: {ex}")
        UKSAuditLogger.info(f"PULLS_COUNT_UPDATE_FAILED | repo_id={repo.id} | error={ex}")
    finally:
        UKSLogger.debug(f"update_pulls_count ended for repo_id={repo.id}")