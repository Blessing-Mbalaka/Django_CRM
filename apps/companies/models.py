from django.core.exceptions import ValidationError
from django.db import models

from .tenancy import CompanyManager, current_company_id, owned_company_id, validate_company_links


class Company(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=60, unique=True, verbose_name='Company code')
    email = models.EmailField(blank=True)
    is_active = models.BooleanField(default=True)
    is_original = models.BooleanField(default=False, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Companies'

    def __str__(self):
        return self.name


class CompanyOwnedModel(models.Model):
    company = models.ForeignKey(Company, on_delete=models.PROTECT, default=owned_company_id, editable=False)
    objects = CompanyManager()
    all_companies = models.Manager()

    class Meta:
        abstract = True

    def validate_company(self):
        current = current_company_id()
        if current and self.company_id != current:
            raise ValidationError({'company': 'This record belongs to another company.'})
        if self.pk and not self._state.adding:
            stored = type(self)._base_manager.filter(pk=self.pk).values_list('company_id', flat=True).first()
            if stored and stored != self.company_id:
                raise ValidationError({'company': 'Company ownership cannot be changed.'})
        validate_company_links(type(self), self.company_id, {
            field.attname: getattr(self, field.attname) for field in self._meta.concrete_fields if field.is_relation
        })

    def save(self, *args, **kwargs):
        self.validate_company()
        return super().save(*args, **kwargs)
