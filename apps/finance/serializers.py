from apps.companies.serializers import CompanyModelSerializer
from rest_framework import serializers
from apps.finance.models import FinancialRecord


class FinancialRecordSerializer(CompanyModelSerializer):
    record_type_display = serializers.SerializerMethodField()
    engagement_title    = serializers.SerializerMethodField()

    class Meta:
        model = FinancialRecord
        fields = [
            'id', 'engagement', 'engagement_title',
            'record_type', 'record_type_display',
            'amount', 'description', 'date', 'is_paid', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def get_record_type_display(self, obj): return obj.get_record_type_display()
    def get_engagement_title(self, obj):    return str(obj.engagement)

    def validate(self, attrs):
        record_type = attrs.get('record_type', getattr(self.instance, 'record_type', None))
        amount = attrs.get('amount', getattr(self.instance, 'amount', None))
        is_paid = attrs.get('is_paid', getattr(self.instance, 'is_paid', False))
        if record_type != FinancialRecord.RecordType.PIPELINE:
            raise serializers.ValidationError({'record_type': 'Actual revenue and expenses come from the accounting ledger; only pipeline forecasts may be entered here.'})
        if amount is not None and amount <= 0:
            raise serializers.ValidationError({'amount': 'Pipeline amount must be greater than zero.'})
        if is_paid:
            raise serializers.ValidationError({'is_paid': 'Pipeline forecasts cannot be marked paid.'})
        return attrs
