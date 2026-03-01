from django.apps import AppConfig
from django.db.utils import OperationalError, ProgrammingError


class UserConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'user'

    def ready(self):
        try:
            from .bootstrap import ensure_superadmin_exists
            ensure_superadmin_exists()
        except (OperationalError, ProgrammingError):
            pass