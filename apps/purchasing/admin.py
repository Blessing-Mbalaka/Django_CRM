from django.contrib import admin

from .models import GoodsReceipt, GoodsReceiptLine, PurchaseOrder, PurchaseOrderLine, PurchaseSequence, Supplier, SupplierBill

admin.site.register([Supplier, PurchaseOrder, PurchaseOrderLine, GoodsReceipt, GoodsReceiptLine, SupplierBill, PurchaseSequence])
