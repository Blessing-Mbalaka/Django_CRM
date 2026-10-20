from apps.companies.serializers import CompanyModelSerializer
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from functionalities.accounting.services import create_draft_entry
from functionalities.accounting.reconciliation import create_bank_statement
from .models import Account, AccountingPeriod, BankStatement, BankStatementLine, JournalEntry, JournalLine


class AccountSerializer(CompanyModelSerializer):
    class Meta:
        model = Account
        fields = ['id', 'code', 'name', 'account_type', 'system_role', 'is_active']

    def validate(self, attrs):
        role = attrs.get('system_role', getattr(self.instance, 'system_role', None))
        account_type = attrs.get('account_type', getattr(self.instance, 'account_type', None))
        expected = {
            Account.SystemRole.BANK: Account.Type.ASSET,
            Account.SystemRole.ACCOUNTS_RECEIVABLE: Account.Type.ASSET,
            Account.SystemRole.ACCOUNTS_PAYABLE: Account.Type.LIABILITY,
            Account.SystemRole.SALES_REVENUE: Account.Type.REVENUE,
            Account.SystemRole.OUTPUT_VAT: Account.Type.LIABILITY,
            Account.SystemRole.INPUT_VAT: Account.Type.ASSET,
            Account.SystemRole.GENERAL_EXPENSE: Account.Type.EXPENSE,
            Account.SystemRole.INVENTORY: Account.Type.ASSET,
            Account.SystemRole.COST_OF_GOODS_SOLD: Account.Type.EXPENSE,
            Account.SystemRole.PAYROLL_EXPENSE: Account.Type.EXPENSE,
            Account.SystemRole.PAYROLL_PAYABLE: Account.Type.LIABILITY,
            Account.SystemRole.PAYROLL_TAX_PAYABLE: Account.Type.LIABILITY,
        }
        if role and expected.get(role) != account_type:
            raise serializers.ValidationError({'account_type': f'{role.replace("_", " ").title()} must use the {expected[role]} account type.'})
        return attrs


class AccountingPeriodSerializer(CompanyModelSerializer):
    class Meta:
        model = AccountingPeriod
        fields = ['id', 'name', 'start_date', 'end_date', 'is_closed']

    def validate(self, attrs):
        if attrs.get('end_date') and attrs.get('start_date') and attrs['end_date'] < attrs['start_date']:
            raise serializers.ValidationError({'end_date': 'End date cannot precede start date.'})
        return attrs


class JournalLineSerializer(CompanyModelSerializer):
    account_name = serializers.CharField(source='account.name', read_only=True)

    class Meta:
        model = JournalLine
        fields = ['id', 'account', 'account_name', 'description', 'debit', 'credit']
        read_only_fields = ['id']


class JournalEntrySerializer(CompanyModelSerializer):
    lines = JournalLineSerializer(many=True)
    total_debit = serializers.DecimalField(max_digits=16, decimal_places=2, read_only=True)
    total_credit = serializers.DecimalField(max_digits=16, decimal_places=2, read_only=True)

    class Meta:
        model = JournalEntry
        fields = ['id', 'date', 'reference', 'description', 'status', 'source_type', 'source_id', 'reversal_of', 'created_by', 'posted_at', 'created_at', 'total_debit', 'total_credit', 'lines']
        read_only_fields = ['id', 'status', 'reversal_of', 'created_by', 'posted_at', 'created_at']
        # The conditional source uniqueness rule is enforced by the database.
        # DRF otherwise incorrectly requires source_id for manual journals.
        validators = []

    def create(self, validated_data):
        lines = validated_data.pop('lines')
        try:
            return create_draft_entry(lines=lines, user=self.context['request'].user, **validated_data)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc

    def update(self, instance, validated_data):
        raise serializers.ValidationError('Journal entries cannot be edited; use a reversal entry.')


class BankStatementLineInputSerializer(serializers.Serializer):
    transaction_date = serializers.DateField()
    description = serializers.CharField(max_length=255)
    reference = serializers.CharField(max_length=80, required=False, allow_blank=True)
    amount = serializers.DecimalField(max_digits=16, decimal_places=2)


class BankStatementLineSerializer(CompanyModelSerializer):
    is_reconciled = serializers.BooleanField(read_only=True)
    journal_date = serializers.DateField(source='matched_journal_line.entry.date', read_only=True)
    journal_reference = serializers.CharField(source='matched_journal_line.entry.reference', read_only=True)

    class Meta:
        model = BankStatementLine
        fields = ['id', 'statement', 'transaction_date', 'description', 'reference', 'amount', 'is_reconciled', 'matched_journal_line', 'journal_date', 'journal_reference', 'reconciled_by', 'reconciled_at']
        read_only_fields = fields


class BankStatementSerializer(CompanyModelSerializer):
    bank_account_name = serializers.CharField(source='bank_account.name', read_only=True)
    lines = BankStatementLineInputSerializer(many=True, write_only=True)
    statement_lines = BankStatementLineSerializer(source='lines', many=True, read_only=True)
    reconciled_count = serializers.SerializerMethodField()

    class Meta:
        model = BankStatement
        fields = ['id', 'bank_account', 'bank_account_name', 'reference', 'start_date', 'end_date', 'opening_balance', 'closing_balance', 'status', 'created_by', 'created_at', 'reconciled_count', 'lines', 'statement_lines']
        read_only_fields = ['id', 'status', 'created_by', 'created_at']

    def get_reconciled_count(self, obj):
        return sum(1 for line in obj.lines.all() if line.is_reconciled)

    def validate_lines(self, value):
        if not value:
            raise serializers.ValidationError('A bank statement requires at least one transaction.')
        return value

    def validate(self, attrs):
        if BankStatement.objects.filter(bank_account=attrs.get('bank_account'), reference=attrs.get('reference')).exists():
            raise serializers.ValidationError({'reference': 'This statement reference already exists for the selected bank account.'})
        return attrs

    def create(self, validated_data):
        lines = validated_data.pop('lines')
        try:
            return create_bank_statement(lines=lines, user=self.context['request'].user, **validated_data)
        except DjangoValidationError as exc:
            detail = exc.message_dict if hasattr(exc, 'message_dict') else exc.messages
            raise serializers.ValidationError(detail) from exc


class ReconciliationCandidateSerializer(CompanyModelSerializer):
    date = serializers.DateField(source='entry.date', read_only=True)
    reference = serializers.CharField(source='entry.reference', read_only=True)
    description = serializers.CharField(source='entry.description', read_only=True)
    amount = serializers.SerializerMethodField()

    class Meta:
        model = JournalLine
        fields = ['id', 'date', 'reference', 'description', 'amount']

    def get_amount(self, obj):
        return obj.debit - obj.credit
