from django.contrib import admin

from .models import Fulfilment, SalesOrder, SalesOrderLine, SalesSequence

admin.site.register([SalesOrder, SalesOrderLine, Fulfilment, SalesSequence])

