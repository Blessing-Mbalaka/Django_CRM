from django.contrib import admin

from .models import Expense, ExpenseApproval, ExpenseCategory

admin.site.register([ExpenseCategory, Expense, ExpenseApproval])

