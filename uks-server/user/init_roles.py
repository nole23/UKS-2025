from django.contrib.auth.models import Group, Permission

def create_roles():
    from django.contrib.auth.models import Group, Permission

    superadmin, _ = Group.objects.get_or_create(name="Superadmin")
    admin, _ = Group.objects.get_or_create(name="Administrator")
    user, _ = Group.objects.get_or_create(name="OrdinaryUser")

    # permissions
    can_create_official_repo = get_perm("add_repository")
    can_view_analytics = get_perm("view_analytics")
    can_assign_badge = get_perm("assign_badge")

    # samo dodaj one perm koji nisu None
    perms_to_add = [p for p in [can_create_official_repo, can_view_analytics, can_assign_badge] if p]
    if perms_to_add:
        admin.permissions.add(*perms_to_add)

    # superadmin dobija sve permisije
    superadmin.permissions.set(Permission.objects.all())


def get_perm(name):
    return Permission.objects.filter(codename=name).first()