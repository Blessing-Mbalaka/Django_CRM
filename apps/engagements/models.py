from apps.companies.models import CompanyOwnedModel
from django.db import models
from django.utils import timezone


class Engagement(CompanyOwnedModel):
    """A business engagement between JBS and a client."""

    class Status(models.TextChoices):
        PROSPECT = 'prospect', 'Prospect'
        ACTIVE   = 'active',   'Active'
        ON_HOLD  = 'on_hold',  'On Hold'
        CLOSED   = 'closed',   'Closed'
        LOST     = 'lost',     'Lost'

    class Visibility(models.TextChoices):
        PRIVATE       = 'private',       'Private'
        SHARED        = 'shared',        'Shared'
        INSTITUTIONAL = 'institutional', 'Institutional'

    title        = models.CharField(max_length=255)
    client       = models.ForeignKey(
        'clients.Client',
        on_delete=models.CASCADE,
        related_name='engagements',
    )
    centre       = models.ForeignKey(
        'centres.Centre',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='engagements',
        verbose_name='Department',
    )
    lead_owner   = models.ForeignKey(
        'accounts.User',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='led_engagements',
        verbose_name='Lead Owner',
    )
    team_members = models.ManyToManyField(
        'accounts.User',
        blank=True,
        related_name='team_engagements',
    )
    status       = models.CharField(max_length=20, choices=Status.choices, default=Status.PROSPECT)
    visibility   = models.CharField(max_length=20, choices=Visibility.choices, default=Visibility.SHARED)
    start_date   = models.DateField(null=True, blank=True)
    end_date     = models.DateField(null=True, blank=True)
    last_contact = models.DateField(null=True, blank=True, verbose_name='Last Contact Date')
    notes        = models.TextField(blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'Engagement'
        verbose_name_plural = 'Engagements'

    def __str__(self):
        return f'{self.title} — {self.client.name}'

    @property
    def days_since_contact(self):
        if not self.last_contact:
            return None
        return (timezone.now().date() - self.last_contact).days

