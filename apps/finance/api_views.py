from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.api.permissions import IsCEODirectorOrAdmin
from .models import FinancialRecord
from .serializers import FinancialRecordSerializer


class FinancialRecordViewSet(viewsets.ModelViewSet):
    """
    list:   GET  /api/finance/
    create: POST /api/finance/
    retrieve: GET  /api/finance/{id}/
    update: PUT  /api/finance/{id}/
    partial_update: PATCH /api/finance/{id}/
    destroy: DELETE /api/finance/{id}/

    Query params: ?record_type=  ?is_paid=true|false  ?engagement=
    """
    serializer_class = FinancialRecordSerializer
    queryset = FinancialRecord.objects.select_related('engagement').order_by('-date')

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [IsAuthenticated()]
        return [IsCEODirectorOrAdmin()]

    def get_queryset(self):
        qs = super().get_queryset().filter(record_type=FinancialRecord.RecordType.PIPELINE)
        p = self.request.query_params
        if record_type := p.get('record_type'):
            qs = qs.filter(record_type=record_type)
        if is_paid := p.get('is_paid'):
            qs = qs.filter(is_paid=(is_paid.lower() == 'true'))
        if engagement := p.get('engagement'):
            qs = qs.filter(engagement_id=engagement)
        return qs
