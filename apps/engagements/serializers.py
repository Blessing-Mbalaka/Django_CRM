from rest_framework import serializers
from apps.engagements.models import Engagement


class EngagementSerializer(serializers.ModelSerializer):
    status_display     = serializers.SerializerMethodField()
    client_name        = serializers.SerializerMethodField()
    lead_name          = serializers.SerializerMethodField()
    days_since_contact = serializers.ReadOnlyField()

    class Meta:
        model = Engagement
        fields = [
            'id', 'title', 'client', 'client_name', 'centre',
            'lead_owner', 'lead_name', 'status', 'status_display',
            'visibility', 'start_date', 'end_date', 'last_contact',
            'days_since_contact', 'notes', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_status_display(self, obj): return obj.get_status_display()
    def get_client_name(self, obj):    return str(obj.client)
    def get_lead_name(self, obj):      return obj.lead_owner.get_full_name() if obj.lead_owner else None
