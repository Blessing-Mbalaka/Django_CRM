from django.db import models


class CommunicationLog(models.Model):
    """Record of every interaction with a client/engagement."""

    class ContactType(models.TextChoices):
        EMAIL   = 'email',   'Email'
        CALL    = 'call',    'Phone Call'
        MEETING = 'meeting', 'Meeting'
        NOTE    = 'note',    'Internal Note'
        OTHER   = 'other',   'Other'

    engagement   = models.ForeignKey(
        'engagements.Engagement',
        on_delete=models.CASCADE,
        related_name='communication_logs',
    )
    logged_by    = models.ForeignKey(
        'accounts.User',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='communication_logs',
    )
    contact_type = models.CharField(max_length=20, choices=ContactType.choices)
    summary      = models.TextField()
    contact_date = models.DateField()
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-contact_date']
        verbose_name = 'Communication Log'
        verbose_name_plural = 'Communication Logs'

    def __str__(self):
        return f'{self.get_contact_type_display()} — {self.engagement} ({self.contact_date})'

