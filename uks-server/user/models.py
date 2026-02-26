from django.contrib.auth.models import Permission, AbstractUser
from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid


class User(AbstractUser):
    """
    Extends Django built-in user.
    """
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    must_change_password = models.BooleanField(default=False)

    # permissions: User ↔ Permission (many-to-many)
    user_permissions = models.ManyToManyField(
        Permission,
        blank=True,
        related_name="dockerhub_users"
    )

    @property
    def is_superadmin(self):
        return self.groups.filter(name="Superadmin").exists()
    
    def is_admin(self):
        return self.groups.filter(name="Administrator").exists()

    def __str__(self):
        return self.username


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile"
    )

    bio = models.TextField(blank=True)
    avatar = models.ImageField(
        upload_to="avatars/",
        blank=True,
        null=True
    )

    # Dodaj polja za kompaniju i druge informacije
    company_name = models.CharField(max_length=255, blank=True)
    company_email = models.EmailField(blank=True)
    company_location = models.CharField(max_length=255, blank=True)
    company_website = models.URLField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    default_repository = models.BooleanField(default=True)

    def __str__(self):
        return f"Profile({self.user.username})"


class PersonalToken(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="personal_tokens"
    )
    name = models.CharField(max_length=255)
    token = models.CharField(max_length=255, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)  # optional

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = uuid.uuid4().hex  # generiše random token
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.user.username})"


# -------------------
# Signal za automatsko kreiranje profila
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)