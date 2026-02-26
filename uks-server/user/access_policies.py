from .permissions import has_required_role


class AccessPolicy:

    @staticmethod
    def can_view_user(viewer, target):

        if has_required_role(viewer, ["Superadmin"]):
            return True

        if has_required_role(viewer, ["Administrator"]):
            if has_required_role(target, ["Superadmin"]):
                return False
            return True

        return viewer.id == target.id


    @staticmethod
    def scope_user_queryset(viewer, qs):

        if has_required_role(viewer, ["Superadmin"]):
            return qs

        if has_required_role(viewer, ["Administrator"]):
            return qs.exclude(groups__name="Superadmin")

        return qs.filter(id=viewer.id)