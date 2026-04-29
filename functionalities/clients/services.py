"""
functionalities/clients/services.py
All business logic for client management.
Views must NOT contain ORM queries — delegate here.
"""
from apps.clients.models import Client


# ── Visibility ──────────────────────────────────────────────────────────────

def apply_visibility_filter(queryset, user):
    """
    Enforce visibility rules:
      - Dean / Admin  → see everything
      - Director/Lead → see institutional + shared + their own private
      - Staff/Analyst → see institutional + shared
    """
    if user.role in ('dean', 'admin'):
        return queryset

    if user.role in ('director', 'lead'):
        return queryset.filter(
            visibility__in=('institutional', 'shared')
        ) | queryset.filter(visibility='private', lead_owner=user)

    # staff, analyst
    return queryset.filter(visibility__in=('institutional', 'shared'))


# ── Queries ──────────────────────────────────────────────────────────────────

def get_client_list(user, search=None, sector=None, centre=None):
    """
    Return a visibility-filtered, optionally searched queryset of clients.
    """
    qs = Client.objects.select_related('centre', 'lead_owner').order_by('name')
    qs = apply_visibility_filter(qs, user)

    if search:
        qs = qs.filter(name__icontains=search)
    if sector:
        qs = qs.filter(sector=sector)
    if centre:
        qs = qs.filter(centre_id=centre)
    return qs


def get_client_detail(pk, user):
    """
    Return a single client with its engagements.
    Raises Client.DoesNotExist if not found or not visible.
    """
    qs = apply_visibility_filter(
        Client.objects.prefetch_related('engagements__lead_owner'), user
    )
    return qs.get(pk=pk)


# ── Mutations ────────────────────────────────────────────────────────────────

def create_client(form, user):
    """
    Save a new client, auto-assigning lead_owner to the requesting user
    if not explicitly set in the form.
    Returns the saved Client instance.
    """
    client = form.save(commit=False)
    if not client.lead_owner_id:
        client.lead_owner = user
    client.save()
    return client


def update_client(form):
    """Save changes to an existing client. Returns the updated instance."""
    return form.save()


def delete_client(client):
    """Delete a client record."""
    client.delete()
