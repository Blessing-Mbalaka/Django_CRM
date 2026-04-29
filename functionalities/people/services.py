"""
functionalities/people/services.py
Staff directory and people management logic.
"""
from apps.staff.models import StaffProfile
from apps.accounts.models import User


def get_staff_directory(centre_id=None, is_active=True, search=None):
    """
    Return a filtered staff profile queryset.
    """
    qs = StaffProfile.objects.select_related('user', 'centre')
    if is_active is not None:
        qs = qs.filter(is_active=is_active)
    if centre_id:
        qs = qs.filter(centre_id=centre_id)
    if search:
        qs = qs.filter(
            user__first_name__icontains=search
        ) | qs.filter(user__last_name__icontains=search)
    return qs.order_by('user__last_name', 'user__first_name')


def get_staff_by_role(role):
    """Return User queryset filtered by role, ordered by name."""
    return User.objects.filter(role=role).order_by('last_name', 'first_name')


def get_directors():
    return get_staff_by_role(User.Role.DIRECTOR)


def get_engagement_leads():
    return get_staff_by_role(User.Role.LEAD)


def get_all_users_for_select():
    """
    Return a lightweight User queryset suitable for form dropdowns
    (id, full name, role).
    """
    return User.objects.filter(is_active=True).order_by('last_name', 'first_name')
