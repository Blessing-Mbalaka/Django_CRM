from django.contrib import admin

from .models import GoodsReceipt, PurchaseOrder, PurchaseOrderLine, PurchaseSequence, Supplier

admin.site.register([Supplier, PurchaseOrder, PurchaseOrderLine, GoodsReceipt, PurchaseSequence])

