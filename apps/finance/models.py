from django.db import models


class FinancialRecord(models.Model):
    """Revenue and pipeline financial tracking per engagement."""

    class RecordType(models.TextChoices):
        REVENUE  = 'revenue',  'Confirmed Revenue'
        PIPELINE = 'pipeline', 'Pipeline (Estimated)'
        EXPENSE  = 'expense',  'Expense'

    engagement  = models.ForeignKey(
        'engagements.Engagement',
        on_delete=models.CASCADE,
        related_name='financial_records',
    )
    record_type = models.CharField(max_length=20, choices=RecordType.choices)
    amount      = models.DecimalField(max_digits=14, decimal_places=2)
    description = models.CharField(max_length=255, blank=True)
    date        = models.DateField()
    is_paid     = models.BooleanField(default=False)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']
        verbose_name = 'Financial Record'
        verbose_name_plural = 'Financial Records'

    def __str__(self):
        return f'{self.get_record_type_display()} — R{self.amount} ({self.engagement})'

