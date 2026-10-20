from apps.companies.serializers import CompanyModelSerializer
from rest_framework import serializers
from .models import CommunicationLog


class CommunicationLogSerializer(CompanyModelSerializer):
    engagement_title    = serializers.SerializerMethodField()
    logged_by_name      = serializers.SerializerMethodField()
    contact_type_display = serializers.SerializerMethodField()

    class Meta:
        model = CommunicationLog
        fields = [
            'id', 'engagement', 'engagement_title',
            'logged_by', 'logged_by_name',
            'contact_type', 'contact_type_display',
            'summary', 'contact_date', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def get_engagement_title(self, obj):     return str(obj.engagement)
    def get_logged_by_name(self, obj):       return obj.logged_by.get_full_name() if obj.logged_by else None
    def get_contact_type_display(self, obj): return obj.get_contact_type_display()
