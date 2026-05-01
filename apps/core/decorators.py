"""
apps/core/decorators.py
Role-based access control decorators for CRM views.

Usage:
    from apps.core.decorators import role_required

    @login_required
    @role_required('dean', 'admin', 'director')
    def my_view(request):
        ...
"""
from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect


def role_required(*allowed_roles):
    """
    Decorator that restricts a view to users whose role is in allowed_roles.
    Redirects to the previous page (or dashboard) with an error message if denied.
    Must be used AFTER @login_required so request.user is always authenticated.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if request.user.is_superuser or request.user.role in allowed_roles:
                return view_func(request, *args, **kwargs)
            messages.error(
                request,
                'You do not have permission to perform that action.',
            )
            # Redirect back or fall through to dashboard
            return redirect(request.META.get('HTTP_REFERER') or 'core:dashboard')
        return _wrapped
    return decorator


# Pre-composed shorthand decorators
# ── Executive: dean + admin only (centres, system config) ─────────────────
def exec_required(view_func):
    return role_required('dean', 'admin')(view_func)


# ── Management: dean + admin + director (finance, staff, centre ops) ──────
def management_required(view_func):
    return role_required('dean', 'admin', 'director')(view_func)


# ── Operational: everyone except pure staff/analyst read-only roles ────────
def operational_required(view_func):
    return role_required('dean', 'admin', 'director', 'lead')(view_func)
