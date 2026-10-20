from apps.companies.serializers import CompanyModelSerializer
from rest_framework import serializers
from .models import StaffProfile


class StaffProfileSerializer(CompanyModelSerializer):
    user_name   = serializers.SerializerMethodField()
    centre_name = serializers.SerializerMethodField()
    email       = serializers.SerializerMethodField()
    role        = serializers.SerializerMethodField()
    department  = serializers.IntegerField(source='centre_id', read_only=True)
    department_name = serializers.CharField(source='centre.name', read_only=True)

    class Meta:
        model = StaffProfile
        fields = [
            'id', 'user', 'user_name', 'email', 'role',
            'department', 'department_name', 'centre', 'centre_name', 'bio', 'expertise',
            'is_active', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def get_user_name(self, obj):   return obj.user.get_full_name()
    def get_email(self, obj):       return obj.user.email
    def get_role(self, obj):        return obj.user.get_role_display()
    def get_centre_name(self, obj): return str(obj.centre) if obj.centre else None
