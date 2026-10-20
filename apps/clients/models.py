from apps.companies.models import CompanyOwnedModel
from django.db import models


class Client(CompanyOwnedModel):
    """Institutional client or stakeholder organisation."""

    class Visibility(models.TextChoices):
        PRIVATE       = 'private',       'Private (Assigned Staff Only)'
        SHARED        = 'shared',        'Shared (Department Level)'
        INSTITUTIONAL = 'institutional', 'Institutional (CEO Access)'

    class Sector(models.TextChoices):
        PUBLIC   = 'public',   'Public Sector'
        PRIVATE  = 'private',  'Private Sector'
        NGO      = 'ngo',      'NGO / Non-profit'
        ACADEMIC = 'academic', 'Academic'
        OTHER    = 'other',    'Other'

    name       = models.CharField(max_length=255)
    sector     = models.CharField(max_length=20, choices=Sector.choices, default=Sector.OTHER)
    ownership  = models.CharField(max_length=120, blank=True, help_text='Ownership structure')
    website    = models.URLField(blank=True)
    notes      = models.TextField(blank=True)
    visibility = models.CharField(max_length=20, choices=Visibility.choices, default=Visibility.SHARED)
    centre     = models.ForeignKey(
        'centres.Centre',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='clients',
        verbose_name='Department',
    )
    lead_owner = models.ForeignKey(
        'accounts.User',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='owned_clients',
        verbose_name='Relationship Owner',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Client'
        verbose_name_plural = 'Clients'

    def __str__(self):
        return self.name

