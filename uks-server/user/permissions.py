from rest_framework.permissions import BasePermission

ROLE_HIERARCHY = {
    "Superadmin": ["Superadmin", "Administrator", "OrdinaryUser"],
    "Administrator": ["Administrator", "OrdinaryUser"],
    "OrdinaryUser": ["OrdinaryUser"],
}


def get_user_roles(user):
    if not user or not user.is_authenticated:
        return []
    return list(user.groups.values_list("name", flat=True))


def has_required_role(user, allowed_roles):
    user_roles = get_user_roles(user)

    for role in user_roles:
        inherited = ROLE_HIERARCHY.get(role, [])
        if any(r in inherited for r in allowed_roles):
            return True
    return False


# -------- BASE --------
class RolePermission(BasePermission):
    allowed_roles = []

    def has_permission(self, request, view):
        return has_required_role(request.user, self.allowed_roles)


# -------- ROLES --------
class IsSuperAdmin(RolePermission):
    allowed_roles = ["Superadmin"]


class IsAdmin(RolePermission):
    allowed_roles = ["Administrator"]


class IsAdminOrSuperAdmin(RolePermission):
    allowed_roles = ["Administrator", "Superadmin"]


class IsUser(RolePermission):
    allowed_roles = ["OrdinaryUser", "Administrator", "Superadmin"]


class IsAdminOrSelf(BasePermission):

    def has_object_permission(self, request, view, obj):
        user = request.user

        if user.is_superadmin:
            return True

        if user.is_admin():
            return True

        return obj == user


# -------- POLICY --------
class MustChangePasswordBlocker(BasePermission):
    def has_permission(self, request, view):
        return not getattr(request.user, "must_change_password", False)