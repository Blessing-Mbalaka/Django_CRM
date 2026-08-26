from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Extended User model with JBS role-based access control.
    Roles determine dashboard view, data visibility, and permissions.
    """

    class Role(models.TextChoices):
        CEO           = 'dean',        'CEO (Executive)'
        DIRECTOR      = 'director',    'Department Director'
        LEAD          = 'lead',        'Engagement Lead'
        ANALYST       = 'analyst',     'Analyst'
        STAFF         = 'staff',       'General Staff'
        ADMIN         = 'admin',       'System Administrator'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STAFF,
        verbose_name='System Role',
    )

    phone = models.CharField(max_length=20, blank=True, verbose_name='Phone')
    job_title = models.CharField(max_length=120, blank=True, verbose_name='Job Title')
    centre = models.ForeignKey(
        'centres.Centre',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='users',
        verbose_name='Department',
    )
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f'{self.get_full_name()} ({self.get_role_display()})'

    @property
    def is_ceo(self):
        return self.role == self.Role.CEO

    @property
    def is_dean(self):
        """Compatibility alias for integrations using the former role name."""
        return self.is_ceo

    @property
    def is_director(self):
        return self.role == self.Role.DIRECTOR

    @property
    def initials(self):
        parts = [self.first_name[:1], self.last_name[:1]]
        return ''.join(p.upper() for p in parts if p)

