from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.api.permissions import IsCEODirectorOrAdmin
from .models import Product
from .serializers import ProductSerializer


class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    queryset = Product.objects.all()

    def get_permissions(self):
        return [IsAuthenticated()] if self.action in ('list', 'retrieve') else [IsCEODirectorOrAdmin()]

    def get_queryset(self):
        qs = super().get_queryset()
        if product_type := self.request.query_params.get('type'):
            qs = qs.filter(product_type=product_type)
        return qs
