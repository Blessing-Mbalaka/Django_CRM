from django.contrib import admin

from .models import Account, AccountingPeriod, JournalEntry, JournalLine

admin.site.register([Account, AccountingPeriod, JournalEntry, JournalLine])

