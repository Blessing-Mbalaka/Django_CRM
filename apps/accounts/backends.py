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
        try:
            user = User.objects.get(
                Q(username__iexact=username) | Q(email__iexact=username)
            )
        except User.MultipleObjectsReturned:
            # If two accounts share the same email, prefer the exact match
            user = User.objects.filter(email__iexact=username).order_by('id').first()
        except User.DoesNotExist:
            return None

        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
