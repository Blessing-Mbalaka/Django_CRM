from django.apps import AppConfig
from django.db.models.signals import m2m_changed, post_migrate


class CompaniesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.companies'

    def ready(self):
        from .tenancy import validate_company_m2m
        for model in self.apps.get_models():
            for field in model._meta.local_many_to_many:
                m2m_changed.connect(validate_company_m2m, sender=field.remote_field.through,
                                    dispatch_uid=f'company.{field.remote_field.through._meta.label}')
        post_migrate.connect(ensure_original_company, sender=self, dispatch_uid='companies.original')


def ensure_original_company(sender, using, **kwargs):
    from .models import Company
    Company.objects.using(using).get_or_create(
        pk=1, defaults={'slug': 'original', 'name': 'Original Company', 'is_original': True},
    )
