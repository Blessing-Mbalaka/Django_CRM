from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.api.permissions import IsCEOOrAdmin
from .models import Centre
from .serializers import CentreSerializer


class CentreViewSet(viewsets.ModelViewSet):
    """
    Department CRUD is exposed at /api/v1/departments/.
    The former /api/v1/centres/ route remains as a compatibility alias.

    Query params: ?is_active=true|false  ?director=
    """
    serializer_class = CentreSerializer
    queryset = Centre.objects.select_related('director').order_by('name')

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsCEOOrAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        qs = super().get_queryset()
        p = self.request.query_params
        if is_active := p.get('is_active'):
            qs = qs.filter(is_active=(is_active.lower() == 'true'))
        if director := p.get('director'):
            qs = qs.filter(director_id=director)
        return qs
