from django.contrib import admin

from .models import PayrollEmployee, PayRun, Payslip

admin.site.register([PayrollEmployee, PayRun, Payslip])
