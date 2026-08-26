from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.api.permissions import IsCEODirectorOrAdmin
from apps.accounts.serializers import UserSerializer
from .models import Engagement
from .serializers import EngagementSerializer


class EngagementViewSet(viewsets.ModelViewSet):
    """
    list:   GET  /api/engagements/
    create: POST /api/engagements/
    retrieve: GET  /api/engagements/{id}/
    update: PUT  /api/engagements/{id}/
    partial_update: PATCH /api/engagements/{id}/
    destroy: DELETE /api/engagements/{id}/

    Query params: ?status=  ?department=  ?client=  ?lead_owner= (`centre` remains supported)

    Extra:
        GET /api/engagements/{id}/team/   → list team members
    """
    serializer_class = EngagementSerializer
    queryset = (
        Engagement.objects
        .select_related('client', 'centre', 'lead_owner')
        .prefetch_related('team_members')
        .order_by('-updated_at')
    )

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsCEODirectorOrAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        qs = super().get_queryset()
        p = self.request.query_params
        if status := p.get('status'):
            qs = qs.filter(status=status)
        if centre := p.get('department') or p.get('centre'):
            qs = qs.filter(centre_id=centre)
        if client := p.get('client'):
            qs = qs.filter(client_id=client)
        if lead_owner := p.get('lead_owner'):
            qs = qs.filter(lead_owner_id=lead_owner)
        return qs

    @action(detail=True, methods=['get'], url_path='team')
    def team(self, request, pk=None):
        """GET /api/engagements/{id}/team/ — list team members for this engagement."""
        engagement = self.get_object()
        serializer = UserSerializer(
            engagement.team_members.all(),
            many=True,
            context={'request': request},
        )
        return Response(serializer.data)
