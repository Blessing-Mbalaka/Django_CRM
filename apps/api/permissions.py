"""
JBS CRM — Shared DRF Permission Classes
Role-based access control for all API endpoints.
"""
from rest_framework.permissions import BasePermission, IsAuthenticated  # noqa: F401


class IsCEOOrAdmin(BasePermission):
    """Full system control: CEO and System Administrators only."""
    message = 'Access restricted to the CEO and System Administrators.'

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.is_superuser or request.user.role in ('dean', 'admin'))
        )


class IsCEODirectorOrAdmin(BasePermission):
    """Operational write access: CEO, Department Directors, and Administrators."""
    message = 'Access restricted to the CEO, Department Directors, and Administrators.'

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.is_superuser or request.user.role in ('dean', 'director', 'admin'))
        )


class IsAuthenticatedReadOnly(BasePermission):
    """
    Any authenticated user may read (GET, HEAD, OPTIONS).
    Writes require additional permission classes.
    """
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        return request.method in ('GET', 'HEAD', 'OPTIONS')


# Compatibility aliases for extensions using the former permission names.
IsDeanOrAdmin = IsCEOOrAdmin
IsDeanDirectorOrAdmin = IsCEODirectorOrAdmin
