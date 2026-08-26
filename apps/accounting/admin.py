from django.contrib import admin

from .models import Account, AccountingPeriod, BankStatement, BankStatementLine, JournalEntry, JournalLine

admin.site.register([Account, AccountingPeriod, BankStatement, BankStatementLine, JournalEntry, JournalLine])
