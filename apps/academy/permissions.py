from rest_framework.permissions import BasePermission


MANAGER_ROLES = {'admin', 'dean'}


def is_academy_manager(user):
    return bool(
        user
        and user.is_authenticated
        and (
            user.is_superuser
            or user.is_staff
            or getattr(user, 'role', None) in MANAGER_ROLES
        )
    )


class IsAcademyManager(BasePermission):
    message = 'Academy management access is required.'

    def has_permission(self, request, view):
        return is_academy_manager(request.user)
