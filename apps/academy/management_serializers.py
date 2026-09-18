from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import (
    AcademyEvent, AcademyResource, AcademyResourceCategory, Course, CourseCategory,
    CourseLevel, CourseModule, Diagnostic, DiagnosticCategory, DiagnosticOption,
    DiagnosticQuestion, DiagnosticRecommendation, EventCategory, ForumCategory,
    ForumPost, FundingOpportunity, LearningPath, MentorProfile, OpportunityCategory,
)


class CleanModelSerializer(serializers.ModelSerializer):
    """Run model validation for rules shared with Admin and CSV imports."""

    def validate(self, attrs):
        values = {}
        if self.instance:
            values = {
                field.name: getattr(self.instance, field.name)
                for field in self.instance._meta.fields
                if field.name != 'id'
            }
        values.update(attrs)
        candidate = self.Meta.model(**values)
        if self.instance:
            candidate.pk = self.instance.pk
        try:
            candidate.full_clean(exclude=['id'], validate_unique=False)
        except DjangoValidationError as exc:
            detail = exc.message_dict if hasattr(exc, 'message_dict') else {'non_field_errors': exc.messages}
            raise serializers.ValidationError(detail) from exc
        return attrs


class NamedCategoryManagementSerializer(CleanModelSerializer):
    class Meta:
        fields = ['id', 'name', 'slug', 'position', 'is_active']


class CourseCategoryManagementSerializer(NamedCategoryManagementSerializer):
    class Meta(NamedCategoryManagementSerializer.Meta): model = CourseCategory


class CourseLevelManagementSerializer(NamedCategoryManagementSerializer):
    class Meta(NamedCategoryManagementSerializer.Meta): model = CourseLevel


class ResourceCategoryManagementSerializer(NamedCategoryManagementSerializer):
    class Meta(NamedCategoryManagementSerializer.Meta): model = AcademyResourceCategory


class DiagnosticCategoryManagementSerializer(NamedCategoryManagementSerializer):
    class Meta(NamedCategoryManagementSerializer.Meta): model = DiagnosticCategory


class OpportunityCategoryManagementSerializer(NamedCategoryManagementSerializer):
    class Meta(NamedCategoryManagementSerializer.Meta): model = OpportunityCategory


class EventCategoryManagementSerializer(NamedCategoryManagementSerializer):
    class Meta(NamedCategoryManagementSerializer.Meta): model = EventCategory


class ForumCategoryManagementSerializer(NamedCategoryManagementSerializer):
    class Meta(NamedCategoryManagementSerializer.Meta): model = ForumCategory


class LearningPathManagementSerializer(CleanModelSerializer):
    class Meta:
        model = LearningPath
        fields = ['id', 'slug', 'title', 'description', 'business_stage', 'position', 'is_published', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class CourseManagementSerializer(CleanModelSerializer):
    class Meta:
        model = Course
        fields = ['id', 'path', 'category', 'level_config', 'slug', 'title', 'description', 'learning_outcome', 'instructor_name', 'level', 'duration_minutes', 'passing_grade', 'certificate_enabled', 'position', 'is_published', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class CourseModuleManagementSerializer(CleanModelSerializer):
    class Meta:
        model = CourseModule
        fields = ['id', 'course', 'title', 'module_type', 'body', 'prompt', 'video_url', 'resource_url', 'quiz_options', 'correct_option', 'position', 'is_required', 'is_published', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class AcademyResourceManagementSerializer(CleanModelSerializer):
    class Meta:
        model = AcademyResource
        fields = ['id', 'category', 'slug', 'title', 'description', 'resource_file', 'external_url', 'is_published', 'created_at']
        read_only_fields = ['created_at']


class DiagnosticManagementSerializer(CleanModelSerializer):
    class Meta:
        model = Diagnostic
        fields = ['id', 'slug', 'title', 'version', 'is_published']


class DiagnosticQuestionManagementSerializer(CleanModelSerializer):
    class Meta:
        model = DiagnosticQuestion
        fields = ['id', 'diagnostic', 'category', 'prompt', 'position', 'is_active']


class DiagnosticOptionManagementSerializer(CleanModelSerializer):
    class Meta:
        model = DiagnosticOption
        fields = ['id', 'question', 'label', 'score', 'position', 'is_active']


class DiagnosticRecommendationManagementSerializer(CleanModelSerializer):
    class Meta:
        model = DiagnosticRecommendation
        fields = ['id', 'diagnostic', 'category', 'course', 'minimum_score', 'maximum_score', 'message', 'position', 'is_active']


class FundingOpportunityManagementSerializer(CleanModelSerializer):
    class Meta:
        model = FundingOpportunity
        fields = ['id', 'category', 'slug', 'title', 'provider', 'description', 'eligibility', 'opens_on', 'closes_on', 'application_url', 'contact_email', 'is_published', 'created_at']
        read_only_fields = ['created_at']

    def validate(self, attrs):
        attrs = super().validate(attrs)
        opens = attrs.get('opens_on', getattr(self.instance, 'opens_on', None))
        closes = attrs.get('closes_on', getattr(self.instance, 'closes_on', None))
        if opens and closes and closes < opens:
            raise serializers.ValidationError({'closes_on': 'Closing date must be on or after opening date.'})
        return attrs


class AcademyEventManagementSerializer(CleanModelSerializer):
    class Meta:
        model = AcademyEvent
        fields = ['id', 'category', 'slug', 'title', 'description', 'starts_at', 'ends_at', 'capacity', 'venue', 'meeting_url', 'registration_url', 'is_published']

    def validate(self, attrs):
        attrs = super().validate(attrs)
        starts = attrs.get('starts_at', getattr(self.instance, 'starts_at', None))
        ends = attrs.get('ends_at', getattr(self.instance, 'ends_at', None))
        if starts and ends and ends < starts:
            raise serializers.ValidationError({'ends_at': 'End time must be after the start time.'})
        return attrs


class MentorProfileManagementSerializer(CleanModelSerializer):
    display_name = serializers.SerializerMethodField()

    class Meta:
        model = MentorProfile
        fields = ['id', 'user', 'display_name', 'expertise', 'industries', 'biography', 'availability', 'is_active']

    def get_display_name(self, obj):
        return obj.user.get_full_name() or obj.user.username

    def validate_user(self, user):
        if self.instance and self.instance.bookings.exists() and user.pk != self.instance.user_id:
            raise serializers.ValidationError('The user cannot change after mentorship bookings exist.')
        return user


class ForumPostModerationSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = ForumPost
        fields = ['id', 'category', 'author', 'author_name', 'title', 'body', 'status', 'is_pinned', 'is_locked', 'created_at', 'updated_at']
        read_only_fields = ['category', 'author', 'author_name', 'title', 'body', 'created_at', 'updated_at']

    def get_author_name(self, obj):
        return obj.author.get_full_name() or obj.author.username
