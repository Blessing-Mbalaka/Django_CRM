from rest_framework import serializers
from apps.centres.models import Centre
from apps.clients.models import Client


class ClientSerializer(serializers.ModelSerializer):
    sector_display     = serializers.SerializerMethodField()
    visibility_display = serializers.SerializerMethodField()
    lead_name          = serializers.SerializerMethodField()
    centre_name        = serializers.SerializerMethodField()
    department         = serializers.PrimaryKeyRelatedField(source='centre', queryset=Centre.objects.all(), required=False, allow_null=True)
    department_name    = serializers.CharField(source='centre.name', read_only=True)

    class Meta:
        model = Client
        fields = [
            'id', 'name', 'sector', 'sector_display', 'ownership', 'website',
            'notes', 'visibility', 'visibility_display',
            'department', 'department_name', 'centre', 'centre_name', 'lead_owner', 'lead_name',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_sector_display(self, obj):    return obj.get_sector_display()
    def get_visibility_display(self, obj): return obj.get_visibility_display()
    def get_lead_name(self, obj):         return obj.lead_owner.get_full_name() if obj.lead_owner else None
    def get_centre_name(self, obj):       return str(obj.centre) if obj.centre else None
