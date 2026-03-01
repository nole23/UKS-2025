from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from .init_roles import create_roles
import secrets
from pathlib import Path

User = get_user_model()


def ensure_superadmin_exists():
    create_roles()

    superadmin_group = Group.objects.get(name="Superadmin")

    if User.objects.filter(groups=superadmin_group).exists():
        return

    password = secrets.token_urlsafe(12)

    user = User.objects.create_superuser(
        username="root",
        email="root@local.com",
        password=password
    )

    user.must_change_password = True
    user.save()
    user.groups.add(superadmin_group)

    # 📁 putanja fajla
    file_path = Path("superadmin_credentials.txt")

    with open(file_path, "w", encoding="utf-8") as f:
        f.write("SUPERADMIN CREATED\n")
        f.write("username: root\n")
        f.write(f"password: {password}\n")
