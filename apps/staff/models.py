from django.db import models


class StaffProfile(models.Model):
    """Extended profile for staff members (linked to User)."""

    user       = models.OneToOneField(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='staff_profile',
    )
    centre     = models.ForeignKey(
        'centres.Centre',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='staff_members',
    )
    bio        = models.TextField(blank=True)
    expertise  = models.CharField(max_length=255, blank=True)
    is_active  = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['user__last_name']
        verbose_name = 'Staff Profile'
        verbose_name_plural = 'Staff Profiles'

    def __str__(self):
        return f'{self.user.get_full_name()} — {self.centre}'

