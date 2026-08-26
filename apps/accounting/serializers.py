from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from functionalities.accounting.services import create_draft_entry
from .models import Account, AccountingPeriod, JournalEntry, JournalLine


class AccountSerializer(serializers.ModelSerializer):
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
        }
        if role and expected.get(role) != account_type:
            raise serializers.ValidationError({'account_type': f'{role.replace("_", " ").title()} must use the {expected[role]} account type.'})
        return attrs


class AccountingPeriodSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountingPeriod
        fields = ['id', 'name', 'start_date', 'end_date', 'is_closed']

    def validate(self, attrs):
        if attrs.get('end_date') and attrs.get('start_date') and attrs['end_date'] < attrs['start_date']:
            raise serializers.ValidationError({'end_date': 'End date cannot precede start date.'})
        return attrs


class JournalLineSerializer(serializers.ModelSerializer):
    account_name = serializers.CharField(source='account.name', read_only=True)

    class Meta:
        model = JournalLine
        fields = ['id', 'account', 'account_name', 'description', 'debit', 'credit']
        read_only_fields = ['id']


class JournalEntrySerializer(serializers.ModelSerializer):
    lines = JournalLineSerializer(many=True)
    total_debit = serializers.DecimalField(max_digits=16, decimal_places=2, read_only=True)
    total_credit = serializers.DecimalField(max_digits=16, decimal_places=2, read_only=True)

    class Meta:
        model = JournalEntry
        fields = ['id', 'date', 'reference', 'description', 'status', 'source_type', 'source_id', 'reversal_of', 'created_by', 'posted_at', 'created_at', 'total_debit', 'total_credit', 'lines']
        read_only_fields = ['id', 'status', 'reversal_of', 'created_by', 'posted_at', 'created_at']

    def create(self, validated_data):
        lines = validated_data.pop('lines')
        try:
            return create_draft_entry(lines=lines, user=self.context['request'].user, **validated_data)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc

    def update(self, instance, validated_data):
        raise serializers.ValidationError('Journal entries cannot be edited; use a reversal entry.')
