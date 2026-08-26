from django.contrib import admin

from .models import Invoice, InvoiceLine, NumberSequence, Payment

admin.site.register([Invoice, InvoiceLine, Payment, NumberSequence])

