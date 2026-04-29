"""
JBS CRM — Shared DRF Permission Classes
Role-based access control for all API endpoints.
"""
from rest_framework.permissions import BasePermission, IsAuthenticated  # noqa: F401


class IsDeanOrAdmin(BasePermission):
    """Full system control — Dean and System Administrators only."""
    message = 'Access restricted to Dean and System Administrators.'

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in ('dean', 'admin')
        )


class IsDeanDirectorOrAdmin(BasePermission):
    """Operational write access — Dean, Centre Directors, and Administrators."""
    message = 'Access restricted to Dean, Directors, and Administrators.'

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in ('dean', 'director', 'admin')
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
