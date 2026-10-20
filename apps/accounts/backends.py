from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

from .models import User


class EmailOrUsernameBackend(ModelBackend):
    """
    Authenticate with either the username field OR the email field.
    Falls back to Django's standard permission checks via ModelBackend.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not password:
            return None
        from apps.companies.tenancy import default_company_id
        company = getattr(request, 'login_company', None) if request else None
        company_id = company.pk if company else default_company_id()
        users = User.objects.filter(company_id=company_id, company__is_active=True)
        exact = users.filter(username=username).first()
        if exact is not None:
            return exact if exact.check_password(password) and self.user_can_authenticate(exact) else None
        try:
            user = users.get(
                Q(username__iexact=username) | Q(email__iexact=username)
            )
        except User.MultipleObjectsReturned:
            # If two accounts share the same email, prefer the exact match
            return None
        except User.DoesNotExist:
            return None

        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
