"""
functionalities/crm_core/services.py
All business logic for the institutional dashboard.
Views must NOT contain business logic — it lives here.
"""
from django.db.models import Count, Sum, Q

# Roles that see the full institutional view
_EXEC_ROLES = ('dean', 'admin')


def _engagement_qs_for_user(user):
    """Return Engagement queryset scoped to the user's visibility level."""
    from apps.engagements.models import Engagement
    qs = Engagement.objects.select_related('client', 'lead_owner', 'centre')
    role = getattr(user, 'role', None)
    if role in _EXEC_ROLES:
        return qs
    if role == 'director':
        centre = getattr(user, 'centre', None)
        return qs.filter(centre=centre) if centre else qs.none()
    # lead / analyst / staff — their own engagements only
    return qs.filter(
        Q(lead_owner=user) | Q(team_members=user)
    ).distinct()


def get_dashboard_context(user):
    """
    Returns aggregated KPIs for the dashboard template.
    Role-aware: CEO/admin see institutional totals; others see scoped data.
    """
    role = getattr(user, 'role', 'staff')
    is_exec = role in _EXEC_ROLES
    is_director = role == 'director'

    context = {
        'total_clients':       0,
        'active_engagements':  0,
        'pipeline_value':      0,
        'alert_count':         0,
        'centres_count':       0,
        'staff_count':         0,
        'recent_engagements':  [],
        'top_alerts':          [],
        'user_role':           role,
        'is_exec':             is_exec,
        'is_director':         is_director,
        'my_centre':           getattr(user, 'centre', None),
        'dashboard_title':     _dashboard_title(role),
    }

    try:
        from apps.clients.models import Client
        if is_exec:
            context['total_clients'] = Client.objects.count()
        elif is_director and user.centre:
            # clients with any engagement in this centre
            context['total_clients'] = Client.objects.filter(
                engagements__centre=user.centre
            ).distinct().count()
        else:
            context['total_clients'] = Client.objects.filter(
                Q(engagements__lead_owner=user) | Q(engagements__team_members=user)
            ).distinct().count()
    except Exception:
        pass

    try:
        eng_qs = _engagement_qs_for_user(user)
        context['active_engagements'] = eng_qs.filter(status='active').count()
        context['recent_engagements'] = eng_qs.order_by('-updated_at')[:5]
    except Exception:
        pass

    try:
        from apps.finance.models import FinancialRecord
        fin_qs = FinancialRecord.objects.filter(record_type='pipeline')
        if not is_exec:
            eng_ids = _engagement_qs_for_user(user).values_list('id', flat=True)
            fin_qs = fin_qs.filter(engagement_id__in=eng_ids)
        result = fin_qs.aggregate(total=Sum('amount'))
        context['pipeline_value'] = result['total'] or 0
    except Exception:
        pass

    try:
        from apps.alerts.models import Alert
        alert_qs = Alert.objects.filter(is_resolved=False)
        if not is_exec and not is_director:
            alert_qs = alert_qs.filter(
                Q(engagement__lead_owner=user) | Q(engagement__team_members=user)
            ).distinct()
        context['alert_count'] = alert_qs.count()
        context['top_alerts'] = alert_qs.order_by('-severity', '-created_at')[:5]
    except Exception:
        pass

    try:
        from apps.centres.models import Centre
        context['centres_count'] = Centre.objects.filter(is_active=True).count()
    except Exception:
        pass

    try:
        from apps.staff.models import StaffProfile
        if is_exec:
            context['staff_count'] = StaffProfile.objects.filter(is_active=True).count()
        elif user.centre:
            context['staff_count'] = StaffProfile.objects.filter(
                is_active=True, centre=user.centre
            ).count()
    except Exception:
        pass

    return context


def _dashboard_title(role):
    titles = {
        'dean':     'CEO Overview',
        'admin':    'Admin Overview',
        'director': 'Director Dashboard',
        'lead':     'My Engagements',
        'analyst':  'My Work',
        'staff':    'My Dashboard',
    }
    return titles.get(role, 'Dashboard')

