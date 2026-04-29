from rest_framework import viewsets

from apps.api.permissions import IsDeanOrAdmin
from apps.accounts.models import User
from apps.accounts.serializers import UserSerializer


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list:     GET /api/users/
    retrieve: GET /api/users/{id}/

    Query params: ?role=  ?centre=  ?is_active=true|false

    Read-only — user creation and management is done via Django Admin.
    Restricted to Dean and System Administrators.
    """
    serializer_class = UserSerializer
    permission_classes = [IsDeanOrAdmin]
    queryset = User.objects.select_related('centre').order_by('last_name', 'first_name')

    def get_queryset(self):
        qs = super().get_queryset()
        p = self.request.query_params
        if role := p.get('role'):
            qs = qs.filter(role=role)
        if centre := p.get('centre'):
            qs = qs.filter(centre_id=centre)
        if is_active := p.get('is_active'):
            qs = qs.filter(is_active=(is_active.lower() == 'true'))
        return qs
