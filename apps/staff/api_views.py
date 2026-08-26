from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import StaffProfile
from .serializers import StaffProfileSerializer


class StaffViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list:     GET /api/staff/
    retrieve: GET /api/staff/{id}/

    Query params: ?department=  ?is_active=true|false (`centre` remains supported)
    """
    serializer_class = StaffProfileSerializer
    permission_classes = [IsAuthenticated]
    queryset = (
        StaffProfile.objects
        .select_related('user', 'centre')
        .order_by('user__last_name', 'user__first_name')
    )

    def get_queryset(self):
        qs = super().get_queryset()
        p = self.request.query_params
        if centre := p.get('department') or p.get('centre'):
            qs = qs.filter(centre_id=centre)
        if is_active := p.get('is_active'):
            qs = qs.filter(is_active=(is_active.lower() == 'true'))
        return qs
