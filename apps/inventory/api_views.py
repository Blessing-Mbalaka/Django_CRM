from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.api.permissions import IsDeanDirectorOrAdmin
from .models import ReorderRule, StockLocation, StockMovement
from .serializers import ReorderRuleSerializer, StockLocationSerializer, StockMovementSerializer


class ManagementWriteViewSet(viewsets.ModelViewSet):
    def get_permissions(self):
        return [IsAuthenticated()] if self.action in ('list', 'retrieve') else [IsDeanDirectorOrAdmin()]


class StockLocationViewSet(ManagementWriteViewSet):
    serializer_class = StockLocationSerializer
    queryset = StockLocation.objects.all()


class StockMovementViewSet(ManagementWriteViewSet):
    serializer_class = StockMovementSerializer
    queryset = StockMovement.objects.select_related('product', 'location', 'created_by')
    http_method_names = ['get', 'post', 'head', 'options']

    def get_queryset(self):
        qs = super().get_queryset()
        if product := self.request.query_params.get('product'):
            qs = qs.filter(product_id=product)
        if location := self.request.query_params.get('location'):
            qs = qs.filter(location_id=location)
        return qs


class ReorderRuleViewSet(ManagementWriteViewSet):
    serializer_class = ReorderRuleSerializer
    queryset = ReorderRule.objects.select_related('product', 'location')

