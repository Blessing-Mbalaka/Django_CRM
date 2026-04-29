from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import CommunicationLog
from .serializers import CommunicationLogSerializer


class CommunicationLogViewSet(viewsets.ModelViewSet):
    """
    list:   GET  /api/communication/
    create: POST /api/communication/
    retrieve: GET  /api/communication/{id}/
    update: PUT  /api/communication/{id}/
    partial_update: PATCH /api/communication/{id}/
    destroy: DELETE /api/communication/{id}/

    Query params: ?engagement=  ?contact_type=  ?logged_by=
    """
    serializer_class = CommunicationLogSerializer
    permission_classes = [IsAuthenticated]
    queryset = (
        CommunicationLog.objects
        .select_related('engagement', 'logged_by')
        .order_by('-contact_date')
    )

    def get_queryset(self):
        qs = super().get_queryset()
        p = self.request.query_params
        if engagement := p.get('engagement'):
            qs = qs.filter(engagement_id=engagement)
        if contact_type := p.get('contact_type'):
            qs = qs.filter(contact_type=contact_type)
        if logged_by := p.get('logged_by'):
            qs = qs.filter(logged_by_id=logged_by)
        return qs

    def perform_create(self, serializer):
        """Auto-assign logged_by to the requesting user if not provided."""
        if not serializer.validated_data.get('logged_by'):
            serializer.save(logged_by=self.request.user)
        else:
            serializer.save()
