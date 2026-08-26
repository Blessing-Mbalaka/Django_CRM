from django.contrib import admin

from .models import ReorderRule, StockLocation, StockMovement

admin.site.register([StockLocation, StockMovement, ReorderRule])

