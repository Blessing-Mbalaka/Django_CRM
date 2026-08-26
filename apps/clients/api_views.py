from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.api.permissions import IsCEODirectorOrAdmin
from .models import Client
from .serializers import ClientSerializer


class ClientViewSet(viewsets.ModelViewSet):
    """
    list:   GET  /api/clients/
    create: POST /api/clients/
    retrieve: GET  /api/clients/{id}/
    update: PUT  /api/clients/{id}/
    partial_update: PATCH /api/clients/{id}/
    destroy: DELETE /api/clients/{id}/

    Query params: ?sector=  ?visibility=  ?department=  ?lead_owner= (`centre` remains supported)
    """
    serializer_class = ClientSerializer
    queryset = Client.objects.select_related('centre', 'lead_owner').order_by('name')

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsCEODirectorOrAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        qs = super().get_queryset()
        p = self.request.query_params
        if sector := p.get('sector'):
            qs = qs.filter(sector=sector)
        if visibility := p.get('visibility'):
            qs = qs.filter(visibility=visibility)
        if centre := p.get('department') or p.get('centre'):
            qs = qs.filter(centre_id=centre)
        if lead_owner := p.get('lead_owner'):
            qs = qs.filter(lead_owner_id=lead_owner)
        return qs
