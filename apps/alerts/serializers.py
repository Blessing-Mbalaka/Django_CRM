from rest_framework import serializers
from apps.alerts.models import Alert


class AlertSerializer(serializers.ModelSerializer):
    severity_display   = serializers.SerializerMethodField()
    alert_type_display = serializers.SerializerMethodField()

    class Meta:
        model = Alert
        fields = [
            'id', 'title', 'description', 'alert_type', 'alert_type_display',
            'severity', 'severity_display', 'engagement', 'client',
            'is_resolved', 'resolved_at', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def get_severity_display(self, obj):   return obj.get_severity_display()
    def get_alert_type_display(self, obj): return obj.get_alert_type_display()
