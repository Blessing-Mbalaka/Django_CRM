from django.contrib.auth.models import UserManager
from apps.companies.tenancy import CompanyQuerySet


class CompanyUserManager(UserManager.from_queryset(CompanyQuerySet)):
    def get_queryset(self):
        return super().get_queryset()._apply_company()
