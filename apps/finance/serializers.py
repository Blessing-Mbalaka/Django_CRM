from rest_framework import serializers
from apps.finance.models import FinancialRecord


class FinancialRecordSerializer(serializers.ModelSerializer):
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
