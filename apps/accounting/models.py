from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Account(models.Model):
    class Type(models.TextChoices):
        ASSET = 'asset', 'Asset'
        LIABILITY = 'liability', 'Liability'
        EQUITY = 'equity', 'Equity'
        REVENUE = 'revenue', 'Revenue'
        EXPENSE = 'expense', 'Expense'

    class SystemRole(models.TextChoices):
        BANK = 'bank', 'Bank / Cash'
        ACCOUNTS_RECEIVABLE = 'accounts_receivable', 'Accounts Receivable'
        ACCOUNTS_PAYABLE = 'accounts_payable', 'Accounts Payable'
        SALES_REVENUE = 'sales_revenue', 'Sales Revenue'
        OUTPUT_VAT = 'output_vat', 'Output VAT'
        INPUT_VAT = 'input_vat', 'Input VAT'
        GENERAL_EXPENSE = 'general_expense', 'General Expense'
        INVENTORY = 'inventory', 'Inventory Asset'

    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=160)
    account_type = models.CharField(max_length=12, choices=Type.choices)
    system_role = models.CharField(max_length=30, choices=SystemRole.choices, null=True, blank=True, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['code']

    def __str__(self):
        return f'{self.code} · {self.name}'


class AccountingPeriod(models.Model):
    name = models.CharField(max_length=80, unique=True)
    start_date = models.DateField()
    end_date = models.DateField()
    is_closed = models.BooleanField(default=False)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return self.name


class JournalEntry(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        POSTED = 'posted', 'Posted'
        REVERSED = 'reversed', 'Reversed'

    date = models.DateField()
    reference = models.CharField(max_length=80, blank=True)
    description = models.CharField(max_length=255)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    source_type = models.CharField(max_length=40, blank=True)
    source_id = models.PositiveBigIntegerField(null=True, blank=True)
    reversal_of = models.OneToOneField('self', null=True, blank=True, on_delete=models.PROTECT, related_name='reversal_entry')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='created_journal_entries')
    posted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-id']

    @property
    def total_debit(self):
        return sum((line.debit for line in self.lines.all()), Decimal('0.00'))

    @property
    def total_credit(self):
        return sum((line.credit for line in self.lines.all()), Decimal('0.00'))

    def __str__(self):
        return self.reference or f'Journal {self.pk}'


class JournalLine(models.Model):
    entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name='lines')
    account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name='journal_lines')
    description = models.CharField(max_length=255, blank=True)
    debit = models.DecimalField(max_digits=16, decimal_places=2, default=0, validators=[MinValueValidator(Decimal('0.00'))])
    credit = models.DecimalField(max_digits=16, decimal_places=2, default=0, validators=[MinValueValidator(Decimal('0.00'))])

    class Meta:
        ordering = ['id']
        constraints = [
            models.CheckConstraint(condition=models.Q(debit__gte=0, credit__gte=0), name='accounting_non_negative_lines'),
        ]


class BankStatement(models.Model):
    class Status(models.TextChoices):
        OPEN = 'open', 'Open'
        RECONCILED = 'reconciled', 'Reconciled'

    bank_account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name='bank_statements')
    reference = models.CharField(max_length=80)
    start_date = models.DateField()
    end_date = models.DateField()
    opening_balance = models.DecimalField(max_digits=16, decimal_places=2)
    closing_balance = models.DecimalField(max_digits=16, decimal_places=2)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.OPEN)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='created_bank_statements')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-end_date', '-id']
        constraints = [models.UniqueConstraint(fields=['bank_account', 'reference'], name='accounting_unique_bank_statement_reference')]

    def __str__(self):
        return f'{self.bank_account.code} - {self.reference}'


class BankStatementLine(models.Model):
    statement = models.ForeignKey(BankStatement, on_delete=models.CASCADE, related_name='lines')
    transaction_date = models.DateField()
    description = models.CharField(max_length=255)
    reference = models.CharField(max_length=80, blank=True)
    amount = models.DecimalField(max_digits=16, decimal_places=2)
    matched_journal_line = models.OneToOneField(JournalLine, null=True, blank=True, on_delete=models.PROTECT, related_name='bank_statement_match')
    reconciled_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name='reconciled_bank_lines')
    reconciled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['transaction_date', 'id']

    @property
    def is_reconciled(self):
        return self.matched_journal_line_id is not None

    def __str__(self):
        return self.reference or self.description
