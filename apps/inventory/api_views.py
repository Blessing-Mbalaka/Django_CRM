import csv
import json
from io import StringIO

from django.forms.models import model_to_dict
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.api.permissions import IsCEODirectorOrAdmin
from apps.products.models import Product
from apps.purchasing.models import Supplier
from functionalities.inventory.maintenance import clear_inventory_data
from functionalities.inventory.queries import inventory_summary, low_stock_rows, product_stock_rows
from functionalities.inventory.reports import REPORT_NAMES, report_dataset, safe_csv_cell
from .models import InventoryCategory, InventorySettings, ProductInventoryProfile, ReorderRule, StockLocation, StockMovement
from .serializers import InventoryCategorySerializer, InventoryProductSerializer, InventorySettingsSerializer, ReorderRuleSerializer, StockLocationSerializer, StockMovementSerializer


class ManagementWriteViewSet(viewsets.ModelViewSet):
    def get_permissions(self):
        return [IsAuthenticated()] if self.action in ('list', 'retrieve') else [IsCEODirectorOrAdmin()]


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
        if movement_type := self.request.query_params.get('movement_type'):
            qs = qs.filter(movement_type=movement_type)
        if date_from := self.request.query_params.get('from'):
            qs = qs.filter(occurred_on__gte=date_from)
        if date_to := self.request.query_params.get('to'):
            qs = qs.filter(occurred_on__lte=date_to)
        if query := self.request.query_params.get('q'):
            qs = qs.filter(product__name__icontains=query) | qs.filter(product__sku__icontains=query) | qs.filter(reference__icontains=query)
        return qs


class ReorderRuleViewSet(ManagementWriteViewSet):
    serializer_class = ReorderRuleSerializer
    queryset = ReorderRule.objects.select_related('product', 'location')


class InventoryCategoryViewSet(ManagementWriteViewSet):
    serializer_class = InventoryCategorySerializer
    queryset = InventoryCategory.objects.all()

    def perform_destroy(self, instance):
        if instance.product_profiles.exists():
            instance.is_active = False
            instance.save(update_fields=['is_active', 'updated_at'])
            return
        instance.delete()


class InventoryProductViewSet(ManagementWriteViewSet):
    serializer_class = InventoryProductSerializer
    queryset = Product.objects.filter(product_type=Product.Type.STOCK).select_related('inventory_profile__category', 'inventory_profile__preferred_supplier')

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.query_params.get('include_archived') != '1':
            qs = qs.filter(is_active=True)
        return qs

    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        product = self.get_object()
        product.is_active = False
        product.save(update_fields=['is_active', 'updated_at'])
        return Response(self.get_serializer(product).data)


class InventorySettingsViewSet(viewsets.ModelViewSet):
    serializer_class = InventorySettingsSerializer
    http_method_names = ['get', 'patch', 'put', 'head', 'options']

    def get_queryset(self):
        InventorySettings.load()
        return InventorySettings.objects.filter(pk=1).order_by('pk')

    def get_permissions(self):
        return [IsAuthenticated()] if self.action in ('list', 'retrieve') else [IsCEODirectorOrAdmin()]


def _movement_data(movement):
    return {'id': movement.id, 'product': movement.product_id, 'product_name': movement.product.name, 'sku': movement.product.sku, 'location': movement.location_id, 'location_name': movement.location.name, 'movement_type': movement.movement_type, 'movement_label': movement.get_movement_type_display(), 'quantity': movement.quantity, 'signed_quantity': movement.signed_quantity, 'unit_cost': movement.unit_cost, 'reference': movement.reference, 'occurred_on': movement.occurred_on}


class InventoryWorkspaceViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        return self.summary(request)

    @action(detail=False)
    def summary(self, request):
        return Response(inventory_summary())

    @action(detail=False, url_path='products')
    def products(self, request):
        return Response(product_stock_rows())

    @action(detail=False, url_path='low-stock')
    def low_stock(self, request):
        return Response(low_stock_rows())

    @action(detail=False)
    def reports(self, request):
        name = request.query_params.get('name', REPORT_NAMES[0])
        try:
            return Response(report_dataset(name))
        except ValueError as exc:
            raise serializers.ValidationError({'name': str(exc)}) from exc

    @action(detail=False, url_path='report.csv')
    def report_csv(self, request):
        try:
            dataset = report_dataset(request.query_params.get('name', REPORT_NAMES[0]))
        except ValueError as exc:
            raise serializers.ValidationError({'name': str(exc)}) from exc
        output = StringIO(newline='')
        writer = csv.writer(output)
        writer.writerow([safe_csv_cell(value) for value in dataset['headers']])
        writer.writerows([[safe_csv_cell(value) for value in row] for row in dataset['rows']])
        response = HttpResponse(output.getvalue(), content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="inventory-report.csv"'
        return response

    @action(detail=False, methods=['get'], permission_classes=[IsCEODirectorOrAdmin])
    def backup(self, request):
        settings = InventorySettings.load()
        data = {
            'version': 1, 'generated_at': timezone.now().isoformat(),
            'settings': model_to_dict(settings),
            'categories': list(InventoryCategory.objects.values()),
            'products': InventoryProductSerializer(Product.objects.filter(product_type=Product.Type.STOCK), many=True).data,
            'suppliers': list(Supplier.objects.values()),
            'locations': list(StockLocation.objects.values()),
            'reorder_rules': list(ReorderRule.objects.values()),
            'movements': [_movement_data(movement) for movement in StockMovement.objects.select_related('product', 'location')],
        }
        response = HttpResponse(json.dumps(data, default=str, indent=2), content_type='application/json')
        response['Content-Disposition'] = 'attachment; filename="inventory-backup.json"'
        return response

    @action(detail=False, methods=['post'], url_path='clear-data', permission_classes=[IsCEODirectorOrAdmin])
    def clear_data(self, request):
        if request.data.get('confirmation') != 'CLEAR INVENTORY DATA':
            raise serializers.ValidationError({'confirmation': 'Enter CLEAR INVENTORY DATA to continue.'})
        return Response(clear_inventory_data(actor=request.user), status=status.HTTP_200_OK)
