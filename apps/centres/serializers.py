from rest_framework import serializers
from apps.centres.models import Centre


class CentreSerializer(serializers.ModelSerializer):
    director_name = serializers.SerializerMethodField()

    class Meta:
        model = Centre
        fields = ['id', 'name', 'code', 'description', 'director', 'director_name', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_director_name(self, obj):
        return obj.director.get_full_name() if obj.director else None
