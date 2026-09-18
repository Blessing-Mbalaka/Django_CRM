from rest_framework import serializers
from django.urls import reverse

from .models import (
    AcademyEvent, AcademyResource, AcademyResourceCategory, Certificate,
    ChatMessage, Conversation, Course, CourseCategory, CourseEnrollment,
    CourseLevel, CourseModule, Diagnostic, DiagnosticCategory,
    DiagnosticOption, DiagnosticQuestion, DiagnosticSubmission, EventCategory,
    EventRegistration, ForumCategory, ForumPost, ForumReply,
    FundingOpportunity, LearningPath, MentorProfile, MentorshipBooking,
    OpportunityCategory,
)


class NamedCategorySerializer(serializers.ModelSerializer):
    class Meta:
        fields = ['id', 'name', 'slug', 'position']
        abstract = True


class CourseCategorySerializer(NamedCategorySerializer):
    class Meta(NamedCategorySerializer.Meta):
        model = CourseCategory


class CourseLevelSerializer(NamedCategorySerializer):
    class Meta(NamedCategorySerializer.Meta):
        model = CourseLevel


class ResourceCategorySerializer(NamedCategorySerializer):
    class Meta(NamedCategorySerializer.Meta):
        model = AcademyResourceCategory


class DiagnosticCategorySerializer(NamedCategorySerializer):
    class Meta(NamedCategorySerializer.Meta):
        model = DiagnosticCategory


class OpportunityCategorySerializer(NamedCategorySerializer):
    class Meta(NamedCategorySerializer.Meta):
        model = OpportunityCategory


class EventCategorySerializer(NamedCategorySerializer):
    class Meta(NamedCategorySerializer.Meta):
        model = EventCategory


class ForumCategorySerializer(NamedCategorySerializer):
    class Meta(NamedCategorySerializer.Meta):
        model = ForumCategory


class LearningPathSummarySerializer(serializers.ModelSerializer):
    stage = serializers.CharField(source='get_business_stage_display', read_only=True)

    class Meta:
        model = LearningPath
        fields = ['slug', 'title', 'description', 'business_stage', 'stage', 'position']


class CourseModuleSerializer(serializers.ModelSerializer):
    type = serializers.CharField(source='module_type', read_only=True)
    video_embed_url = serializers.SerializerMethodField()

    class Meta:
        model = CourseModule
        fields = [
            'id',
            'title',
            'type',
            'body',
            'prompt',
            'video_embed_url',
            'resource_url',
            'quiz_options',
            'position',
            'is_required',
        ]

    def get_video_embed_url(self, module):
        if not module.video_url:
            return ''
        request = self.context.get('request')
        origin = request.build_absolute_uri('/').rstrip('/') if request else ''
        return module.youtube_embed_url(origin)


class CourseListSerializer(serializers.ModelSerializer):
    path = LearningPathSummarySerializer(read_only=True)
    category = CourseCategorySerializer(read_only=True)
    level_config = CourseLevelSerializer(read_only=True)
    level_label = serializers.SerializerMethodField()
    enrollment_status = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            'slug',
            'title',
            'description',
            'learning_outcome',
            'instructor_name',
            'level',
            'level_label',
            'level_config',
            'category',
            'duration_minutes',
            'passing_grade',
            'certificate_enabled',
            'enrollment_status',
            'position',
            'path',
        ]

    def get_level_label(self, course):
        return course.level_config.name if course.level_config else course.get_level_display()

    def get_enrollment_status(self, course):
        enrollments = getattr(course, 'current_user_enrollments', [])
        return enrollments[0].status if enrollments else CourseEnrollment.Status.NOT_STARTED


class CourseDetailSerializer(CourseListSerializer):
    modules = serializers.SerializerMethodField()

    class Meta(CourseListSerializer.Meta):
        fields = CourseListSerializer.Meta.fields + ['modules']

    def get_modules(self, course):
        modules = getattr(course, 'published_modules', course.modules.filter(is_published=True))
        return CourseModuleSerializer(modules, many=True, context=self.context).data


class CertificateSerializer(serializers.ModelSerializer):
    print_url = serializers.SerializerMethodField()

    class Meta:
        model = Certificate
        fields = ['verification_id', 'learner_name', 'course_title', 'grade', 'issued_at', 'print_url']

    def get_print_url(self, certificate):
        return reverse('academy:certificate', kwargs={'verification_id': certificate.verification_id})


class CourseEnrollmentSerializer(serializers.ModelSerializer):
    course = CourseListSerializer(read_only=True)
    certificate = CertificateSerializer(read_only=True)

    class Meta:
        model = CourseEnrollment
        fields = ['id', 'course', 'status', 'final_grade', 'started_at', 'completed_at', 'certificate']


class AcademyResourceSerializer(serializers.ModelSerializer):
    category = ResourceCategorySerializer(read_only=True)
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = AcademyResource
        fields = ['slug', 'title', 'description', 'category', 'download_url', 'external_url', 'created_at']

    def get_download_url(self, resource):
        if not resource.resource_file:
            return ''
        request = self.context.get('request')
        return request.build_absolute_uri(resource.resource_file.url) if request else resource.resource_file.url


class DiagnosticOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiagnosticOption
        fields = ['id', 'label', 'position']


class DiagnosticQuestionSerializer(serializers.ModelSerializer):
    category = DiagnosticCategorySerializer(read_only=True)
    options = DiagnosticOptionSerializer(many=True, read_only=True)

    class Meta:
        model = DiagnosticQuestion
        fields = ['id', 'prompt', 'position', 'category', 'options']


class DiagnosticSerializer(serializers.ModelSerializer):
    questions = DiagnosticQuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Diagnostic
        fields = ['slug', 'title', 'version', 'questions']


class DiagnosticSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiagnosticSubmission
        fields = ['id', 'user', 'diagnostic', 'diagnostic_version', 'answers', 'category_scores', 'recommendations', 'total_score', 'created_at']
        read_only_fields = fields


class FundingOpportunitySerializer(serializers.ModelSerializer):
    category = OpportunityCategorySerializer(read_only=True)

    class Meta:
        model = FundingOpportunity
        fields = ['slug', 'title', 'provider', 'category', 'description', 'eligibility', 'opens_on', 'closes_on', 'application_url', 'contact_email']


class AcademyEventSerializer(serializers.ModelSerializer):
    category = EventCategorySerializer(read_only=True)
    is_registered = serializers.SerializerMethodField()

    class Meta:
        model = AcademyEvent
        fields = ['slug', 'title', 'category', 'description', 'starts_at', 'ends_at', 'capacity', 'venue', 'meeting_url', 'registration_url', 'is_registered']

    def get_is_registered(self, event):
        user = self.context['request'].user
        return event.registrations.filter(user=user).exists()


class EventRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventRegistration
        fields = ['id', 'event', 'user', 'registered_at']
        read_only_fields = fields


class MentorProfileSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = MentorProfile
        fields = ['id', 'name', 'expertise', 'industries', 'biography', 'availability']

    def get_name(self, mentor):
        return mentor.user.get_full_name() or mentor.user.username


class MentorshipBookingSerializer(serializers.ModelSerializer):
    mentor_detail = MentorProfileSerializer(source='mentor', read_only=True)
    learner_name = serializers.SerializerMethodField()
    can_respond = serializers.SerializerMethodField()

    class Meta:
        model = MentorshipBooking
        fields = ['id', 'learner', 'learner_name', 'mentor', 'mentor_detail', 'topic', 'requested_for', 'status', 'can_respond', 'created_at']
        read_only_fields = ['learner', 'status', 'created_at']

    def get_learner_name(self, booking):
        return booking.learner.get_full_name() or booking.learner.username

    def get_can_respond(self, booking):
        request = self.context.get('request')
        return bool(request and booking.mentor.user_id == request.user.id and booking.status == booking.Status.REQUESTED)

    def validate_mentor(self, mentor):
        if not mentor.is_active:
            raise serializers.ValidationError('Choose an active mentor.')
        return mentor


class ChatMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.SerializerMethodField()

    class Meta:
        model = ChatMessage
        fields = ['id', 'conversation', 'sender', 'sender_name', 'body', 'created_at', 'read_at']
        read_only_fields = ['sender', 'sender_name', 'created_at', 'read_at']

    def get_sender_name(self, message):
        return message.sender.get_full_name() or message.sender.username


class ConversationSerializer(serializers.ModelSerializer):
    messages = ChatMessageSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = ['id', 'booking', 'created_at', 'messages']


class ForumReplySerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = ForumReply
        fields = ['id', 'post', 'author', 'author_name', 'body', 'created_at']
        read_only_fields = ['author', 'author_name', 'created_at']

    def get_author_name(self, reply):
        return reply.author.get_full_name() or reply.author.username


class ForumPostSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()
    category_detail = ForumCategorySerializer(source='category', read_only=True)
    replies = ForumReplySerializer(many=True, read_only=True)

    class Meta:
        model = ForumPost
        fields = ['id', 'category', 'category_detail', 'author', 'author_name', 'title', 'body', 'is_pinned', 'is_locked', 'created_at', 'updated_at', 'replies']
        read_only_fields = ['author', 'author_name', 'is_pinned', 'is_locked', 'created_at', 'updated_at', 'replies']

    def get_author_name(self, post):
        return post.author.get_full_name() or post.author.username
