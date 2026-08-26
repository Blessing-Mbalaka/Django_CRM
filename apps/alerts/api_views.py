from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.api.permissions import IsCEODirectorOrAdmin
from .models import Alert
from .serializers import AlertSerializer


class AlertViewSet(viewsets.ModelViewSet):
    """
    list:   GET  /api/alerts/
    create: POST /api/alerts/
    retrieve: GET  /api/alerts/{id}/
    update: PUT  /api/alerts/{id}/
    partial_update: PATCH /api/alerts/{id}/
    destroy: DELETE /api/alerts/{id}/

    Query params: ?severity=  ?is_resolved=true|false  ?alert_type=  ?client=  ?engagement=

    Extra:
        POST /api/alerts/{id}/resolve/  → mark alert resolved
    """
    serializer_class = AlertSerializer
    queryset = Alert.objects.select_related('engagement', 'client').order_by('-created_at')

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsCEODirectorOrAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        qs = super().get_queryset()
        p = self.request.query_params
        if severity := p.get('severity'):
            qs = qs.filter(severity=severity)
        if is_resolved := p.get('is_resolved'):
            qs = qs.filter(is_resolved=(is_resolved.lower() == 'true'))
        if alert_type := p.get('alert_type'):
            qs = qs.filter(alert_type=alert_type)
        if client := p.get('client'):
            qs = qs.filter(client_id=client)
        if engagement := p.get('engagement'):
            qs = qs.filter(engagement_id=engagement)
        return qs

    @action(detail=True, methods=['post'], url_path='resolve')
    def resolve(self, request, pk=None):
        """POST /api/alerts/{id}/resolve/ — mark this alert as resolved."""
        alert = self.get_object()
        if alert.is_resolved:
            return Response({'detail': 'Alert is already resolved.'}, status=200)
        alert.is_resolved = True
        alert.resolved_at = timezone.now()
        alert.save(update_fields=['is_resolved', 'resolved_at'])
        return Response(AlertSerializer(alert, context={'request': request}).data)
