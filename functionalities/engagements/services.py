"""
functionalities/engagements/services.py
All business logic for engagement lifecycle management.
"""
from django.utils import timezone
from apps.engagements.models import Engagement


# ── Visibility ──────────────────────────────────────────────────────────────

def apply_visibility_filter(queryset, user):
    if user.role in ('dean', 'admin'):
        return queryset
    if user.role in ('director', 'lead'):
        return queryset.filter(
            visibility__in=('institutional', 'shared')
        ) | queryset.filter(visibility='private', lead_owner=user)
    return queryset.filter(visibility__in=('institutional', 'shared'))


# ── Queries ──────────────────────────────────────────────────────────────────

def get_engagement_list(user, status=None, centre=None, client=None, search=None):
    """Return visibility-filtered engagements with optional filters."""
    qs = (
        Engagement.objects
        .select_related('client', 'centre', 'lead_owner')
        .order_by('-updated_at')
    )
    qs = apply_visibility_filter(qs, user)

    if status:
        qs = qs.filter(status=status)
    if centre:
        qs = qs.filter(centre_id=centre)
    if client:
        qs = qs.filter(client_id=client)
    if search:
        qs = qs.filter(title__icontains=search)
    return qs


def get_engagement_detail(pk, user):
    """
    Return a single engagement with related data.
    Applies visibility rules.
    """
    qs = apply_visibility_filter(
        Engagement.objects
        .select_related('client', 'centre', 'lead_owner')
        .prefetch_related('team_members', 'financial_records', 'communication_logs__logged_by'),
        user,
    )
    return qs.get(pk=pk)


def check_duplicate_engagement(client_id, centre_id, exclude_pk=None):
    """
    Returns True if an active/prospect engagement already exists for the
    same client+centre combination (overlap detection rule from master plan).
    """
    qs = Engagement.objects.filter(
        client_id=client_id,
        centre_id=centre_id,
        status__in=('prospect', 'active'),
    )
    if exclude_pk:
        qs = qs.exclude(pk=exclude_pk)
    return qs.exists()


# ── Mutations ────────────────────────────────────────────────────────────────

def create_engagement(form, user):
    """
    Save a new engagement.
    - Auto-assigns lead_owner if not set.
    - Returns (engagement, duplicate_warning) tuple.
    """
    eng = form.save(commit=False)
    if not eng.lead_owner_id:
        eng.lead_owner = user

    duplicate = check_duplicate_engagement(
        eng.client_id, eng.centre_id
    ) if eng.client_id and eng.centre_id else False

    eng.save()
    form.save_m2m()
    return eng, duplicate


def update_engagement(form, user):
    """Save changes to an existing engagement. Returns (engagement, duplicate_warning)."""
    eng = form.save(commit=False)
    duplicate = check_duplicate_engagement(
        eng.client_id, eng.centre_id, exclude_pk=eng.pk
    ) if eng.client_id and eng.centre_id else False
    eng.save()
    form.save_m2m()
    return eng, duplicate


def update_last_contact(engagement, contact_date=None):
    """
    Update the last_contact date on an engagement.
    Defaults to today if no date provided.
    """
    engagement.last_contact = contact_date or timezone.now().date()
    engagement.save(update_fields=['last_contact', 'updated_at'])


def delete_engagement(engagement):
    engagement.delete()
