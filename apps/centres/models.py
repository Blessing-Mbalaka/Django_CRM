from django.db import models


class Centre(models.Model):
    """JBS Research / Teaching Centre."""

    name        = models.CharField(max_length=200, unique=True)
    code        = models.CharField(max_length=20, unique=True)
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
        ordering = ['name']
        verbose_name = 'Centre'
        verbose_name_plural = 'Centres'

    def __str__(self):
        return self.name

