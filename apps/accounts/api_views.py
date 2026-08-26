from rest_framework import viewsets

from apps.api.permissions import IsCEOOrAdmin
from apps.accounts.models import User
from apps.accounts.serializers import UserSerializer


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list:     GET /api/users/
    retrieve: GET /api/users/{id}/

    Query params: ?role=  ?department=  ?is_active=true|false (`centre` remains supported)

    Read-only — user creation and management is done via Django Admin.
    Restricted to the CEO and System Administrators.
    """
    serializer_class = UserSerializer
    permission_classes = [IsCEOOrAdmin]
    queryset = User.objects.select_related('centre').order_by('last_name', 'first_name')

    def get_queryset(self):
        qs = super().get_queryset()
        p = self.request.query_params
        if role := p.get('role'):
            qs = qs.filter(role=role)
        if centre := p.get('department') or p.get('centre'):
            qs = qs.filter(centre_id=centre)
        if is_active := p.get('is_active'):
            qs = qs.filter(is_active=(is_active.lower() == 'true'))
        return qs
