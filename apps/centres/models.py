from apps.companies.models import CompanyOwnedModel
from django.db import models


class Centre(CompanyOwnedModel):
    """Organisational department (legacy model name retained for compatibility)."""

    name        = models.CharField(max_length=200)
    code        = models.CharField(max_length=20)
    description = models.TextField(blank=True)
    director    = models.ForeignKey(
        'accounts.User',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='directed_centres',
        verbose_name='Director',
    )
    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['company', 'name'], name='centres_centre_name_company'), models.UniqueConstraint(fields=['company', 'code'], name='centres_centre_code_company')]
        ordering = ['name']
        verbose_name = 'Department'
        verbose_name_plural = 'Departments'

    def __str__(self):
        return self.name

