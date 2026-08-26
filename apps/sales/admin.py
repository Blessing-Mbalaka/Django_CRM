from django.contrib import admin

from .models import Fulfilment, FulfilmentLine, SalesOrder, SalesOrderLine, SalesSequence

admin.site.register([SalesOrder, SalesOrderLine, Fulfilment, FulfilmentLine, SalesSequence])
