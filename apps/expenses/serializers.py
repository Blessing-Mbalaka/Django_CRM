from rest_framework import serializers

from .models import Expense, ExpenseApproval, ExpenseCategory


class ExpenseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseCategory
        fields = ['id', 'name', 'is_active']
        read_only_fields = ['id']


class ExpenseApprovalSerializer(serializers.ModelSerializer):
    decided_by_name = serializers.CharField(source='decided_by.get_full_name', read_only=True)

    class Meta:
        model = ExpenseApproval
        fields = ['id', 'expense', 'decision', 'comment', 'decided_by', 'decided_by_name', 'created_at']
        read_only_fields = fields


class ExpenseSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    submitted_by_name = serializers.CharField(source='submitted_by.get_full_name', read_only=True)
    approvals = ExpenseApprovalSerializer(many=True, read_only=True)

    class Meta:
        model = Expense
        fields = ['id', 'description', 'category', 'category_name', 'amount', 'vat_amount', 'incurred_on', 'payment_method', 'status', 'submitted_by', 'submitted_by_name', 'client', 'engagement', 'receipt_document', 'notes', 'approvals', 'created_at', 'updated_at']
        read_only_fields = ['id', 'status', 'submitted_by', 'created_at', 'updated_at']

    def validate(self, attrs):
        amount = attrs.get('amount', getattr(self.instance, 'amount', None))
        vat_amount = attrs.get('vat_amount', getattr(self.instance, 'vat_amount', 0))
        if amount is not None and vat_amount > amount:
            raise serializers.ValidationError({'vat_amount': 'VAT amount cannot exceed the total expense.'})
        if self.instance and self.instance.status not in (Expense.Status.DRAFT, Expense.Status.REJECTED):
            raise serializers.ValidationError('Only draft or rejected expenses can be edited.')
        return attrs

