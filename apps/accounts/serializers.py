from apps.companies.serializers import CompanyModelSerializer
from rest_framework import serializers
from apps.centres.models import Centre
from .models import User


class UserSerializer(CompanyModelSerializer):
    full_name = serializers.SerializerMethodField()
    role_display = serializers.SerializerMethodField()
    department = serializers.PrimaryKeyRelatedField(source='centre', queryset=Centre.objects.all(), required=False, allow_null=True)
    department_name = serializers.CharField(source='centre.name', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'full_name', 'role', 'role_display', 'phone', 'job_title',
            'department', 'department_name', 'centre', 'is_active', 'date_joined',
        ]
        read_only_fields = ['id', 'date_joined']

    def get_full_name(self, obj):
        return obj.get_full_name()

    def get_role_display(self, obj):
        return obj.get_role_display()
