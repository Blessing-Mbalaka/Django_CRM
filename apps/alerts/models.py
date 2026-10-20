from apps.companies.models import CompanyOwnedModel
from django.db import models


class Alert(CompanyOwnedModel):
    """System-generated risk alerts and notifications."""

    class Severity(models.TextChoices):
        LOW      = 'low',      'Low'
        MEDIUM   = 'medium',   'Medium'
        HIGH     = 'high',     'High'
        CRITICAL = 'critical', 'Critical'

    class AlertType(models.TextChoices):
        NO_CONTACT   = 'no_contact',    'No Contact Risk'
        PAYMENT_DUE  = 'payment_due',   'Payment Overdue'
        DEADLINE     = 'deadline',      'Deadline Approaching'
        DORMANT      = 'dormant',       'Dormant Client'
        OVERLAP      = 'overlap',       'Engagement Overlap'
        SYSTEM       = 'system',        'System Notice'

    title        = models.CharField(max_length=255)
    description  = models.TextField(blank=True)
    alert_type   = models.CharField(max_length=30, choices=AlertType.choices)
    severity     = models.CharField(max_length=20, choices=Severity.choices, default=Severity.MEDIUM)
    engagement   = models.ForeignKey(
        'engagements.Engagement',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='alerts',
    )
    client       = models.ForeignKey(
        'clients.Client',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='alerts',
    )
    is_resolved  = models.BooleanField(default=False)
    resolved_at  = models.DateTimeField(null=True, blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Alert'
        verbose_name_plural = 'Alerts'

    def __str__(self):
        return f'[{self.get_severity_display()}] {self.title}'

    @property
    def severity_color(self):
        return {
            'low':      'secondary',
            'medium':   'warning',
            'high':     'orange',
            'critical': 'danger',
        }.get(self.severity, 'secondary')

