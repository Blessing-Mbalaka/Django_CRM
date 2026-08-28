from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.accounting.models import Account


DEFAULT_ACCOUNTS = (
    ('1000', 'Bank', Account.Type.ASSET, Account.SystemRole.BANK),
    ('1100', 'Accounts Receivable', Account.Type.ASSET, Account.SystemRole.ACCOUNTS_RECEIVABLE),
    ('1200', 'Input VAT', Account.Type.ASSET, Account.SystemRole.INPUT_VAT),
    ('1300', 'Inventory', Account.Type.ASSET, Account.SystemRole.INVENTORY),
    ('2000', 'Accounts Payable', Account.Type.LIABILITY, Account.SystemRole.ACCOUNTS_PAYABLE),
    ('2100', 'Output VAT', Account.Type.LIABILITY, Account.SystemRole.OUTPUT_VAT),
    ('2200', 'Payroll Payable', Account.Type.LIABILITY, Account.SystemRole.PAYROLL_PAYABLE),
    ('2300', 'Payroll Tax / Deductions Payable', Account.Type.LIABILITY, Account.SystemRole.PAYROLL_TAX_PAYABLE),
    ('4000', 'Sales Revenue', Account.Type.REVENUE, Account.SystemRole.SALES_REVENUE),
    ('5000', 'General Expense', Account.Type.EXPENSE, Account.SystemRole.GENERAL_EXPENSE),
    ('5100', 'Cost of Goods Sold', Account.Type.EXPENSE, Account.SystemRole.COST_OF_GOODS_SOLD),
    ('5200', 'Payroll Expense', Account.Type.EXPENSE, Account.SystemRole.PAYROLL_EXPENSE),
)


class Command(BaseCommand):
    help = 'Create the canonical chart of system accounts without overwriting existing accounts.'

    @transaction.atomic
    def handle(self, *args, **options):
        created = 0
        for code, name, account_type, role in DEFAULT_ACCOUNTS:
            account = Account.objects.filter(system_role=role).first()
            if account:
                if account.account_type != account_type:
                    raise CommandError(f'{role} exists with incompatible type {account.account_type}.')
                continue
            if Account.objects.filter(code=code).exists():
                raise CommandError(f'Account code {code} already exists; assign the {role} role manually.')
            Account.objects.create(code=code, name=name, account_type=account_type, system_role=role)
            created += 1
        self.stdout.write(self.style.SUCCESS(f'Canonical system accounts ready ({created} created).'))
