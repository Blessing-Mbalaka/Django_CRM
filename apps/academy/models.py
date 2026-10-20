from apps.companies.models import CompanyOwnedModel
import uuid
from urllib.parse import urlencode

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.conf import settings
from django.utils import timezone

from .validators import extract_youtube_video_id


class LearningPath(models.Model):
    class BusinessStage(models.TextChoices):
        FOUNDATIONS = 'foundations', 'Foundations'
        VALIDATE = 'validate', 'Validate'
        BUILD = 'build', 'Build'
        GROW = 'grow', 'Grow'
        SCALE = 'scale', 'Scale'
        INVESTMENT_READY = 'investment_ready', 'Investment Ready'

    slug = models.SlugField(max_length=80, unique=True)
    title = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    business_stage = models.CharField(max_length=24, choices=BusinessStage.choices)
    position = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['position', 'title']

    def __str__(self):
        return self.title


class CourseCategory(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=120, unique=True)
    position = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['position', 'name']

    def __str__(self):
        return self.name


class CourseLevel(models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=80, unique=True)
    position = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['position', 'name']

    def __str__(self):
        return self.name


class Course(models.Model):
    class Level(models.TextChoices):
        BEGINNER = 'beginner', 'Beginner'
        INTERMEDIATE = 'intermediate', 'Intermediate'
        ADVANCED = 'advanced', 'Advanced'

    path = models.ForeignKey(LearningPath, on_delete=models.PROTECT, related_name='courses')
    category = models.ForeignKey(CourseCategory, null=True, blank=True, on_delete=models.SET_NULL, related_name='courses')
    level_config = models.ForeignKey(CourseLevel, null=True, blank=True, on_delete=models.SET_NULL, related_name='courses')
    slug = models.SlugField(max_length=120, unique=True)
    title = models.CharField(max_length=220)
    description = models.TextField()
    learning_outcome = models.CharField(max_length=255, blank=True)
    instructor_name = models.CharField(max_length=160)
    level = models.CharField(max_length=16, choices=Level.choices, default=Level.BEGINNER)
    duration_minutes = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    passing_grade = models.PositiveSmallIntegerField(
        default=50, validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    certificate_enabled = models.BooleanField(default=True)
    position = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['path__position', 'position', 'title']
        constraints = [
            models.UniqueConstraint(fields=['path', 'position'], name='academy_unique_course_position'),
        ]

    def __str__(self):
        return self.title


class CourseModule(models.Model):
    class Type(models.TextChoices):
        VIDEO = 'video', 'Video'
        ARTICLE = 'article', 'Article'
        ACTIVITY = 'activity', 'Guided activity'
        QUIZ = 'quiz', 'Quiz'
        PRACTICAL = 'practical', 'Practical task'
        RESOURCE = 'resource', 'Resource'
        REFLECTION = 'reflection', 'Reflection'

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=220)
    module_type = models.CharField(max_length=16, choices=Type.choices)
    body = models.TextField(blank=True)
    prompt = models.TextField(blank=True)
    video_url = models.URLField(blank=True)
    resource_url = models.URLField(blank=True)
    quiz_options = models.JSONField(default=list, blank=True)
    correct_option = models.PositiveSmallIntegerField(null=True, blank=True)
    position = models.PositiveIntegerField(default=0)
    is_required = models.BooleanField(default=True)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['position', 'id']
        constraints = [
            models.UniqueConstraint(fields=['course', 'position'], name='academy_unique_module_position'),
        ]

    def __str__(self):
        return f'{self.course.title}: {self.title}'

    def clean(self):
        super().clean()
        errors = {}
        if self.module_type == self.Type.VIDEO:
            if not self.video_url:
                errors['video_url'] = 'Video modules require a YouTube URL.'
            else:
                try:
                    extract_youtube_video_id(self.video_url)
                except ValidationError as exc:
                    errors['video_url'] = exc.messages
        elif self.video_url:
            errors['video_url'] = 'A YouTube URL is only allowed for video modules.'

        if self.module_type == self.Type.QUIZ:
            if len(self.quiz_options) < 2:
                errors['quiz_options'] = 'Quiz modules require at least two options.'
            if self.correct_option is None or self.correct_option >= len(self.quiz_options):
                errors['correct_option'] = 'Choose a correct option from the quiz options.'
        elif self.correct_option is not None:
            errors['correct_option'] = 'A correct option is only allowed for quiz modules.'

        if errors:
            raise ValidationError(errors)

    @property
    def youtube_video_id(self):
        return extract_youtube_video_id(self.video_url) if self.video_url else ''

    def youtube_embed_url(self, origin: str) -> str:
        if not self.video_url:
            return ''
        query = urlencode({'origin': origin.rstrip('/')})
        return f'https://www.youtube-nocookie.com/embed/{self.youtube_video_id}?{query}'


class CourseEnrollment(CompanyOwnedModel):
    class Status(models.TextChoices):
        NOT_STARTED = 'not_started', 'Not started'
        IN_PROGRESS = 'in_progress', 'In progress'
        COMPLETED = 'completed', 'Completed'
        PASSED = 'passed', 'Passed'
        FAILED = 'failed', 'Failed'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='academy_enrollments')
    course = models.ForeignKey(Course, on_delete=models.PROTECT, related_name='enrollments')
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.NOT_STARTED)
    final_grade = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['company', 'user', 'course'], name='academy_unique_enrollment')]


class ModuleProgress(CompanyOwnedModel):
    enrollment = models.ForeignKey(CourseEnrollment, on_delete=models.CASCADE, related_name='module_progress')
    module = models.ForeignKey(CourseModule, on_delete=models.CASCADE, related_name='learner_progress')
    response = models.TextField(blank=True)
    completed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['company', 'enrollment', 'module'], name='academy_unique_module_progress')]


class QuizAttempt(CompanyOwnedModel):
    enrollment = models.ForeignKey(CourseEnrollment, on_delete=models.CASCADE, related_name='quiz_attempts')
    module = models.ForeignKey(CourseModule, on_delete=models.CASCADE, related_name='quiz_attempts')
    selected_option = models.PositiveSmallIntegerField()
    is_correct = models.BooleanField()
    score = models.DecimalField(max_digits=5, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)


class Certificate(CompanyOwnedModel):
    enrollment = models.OneToOneField(CourseEnrollment, on_delete=models.PROTECT, related_name='certificate')
    verification_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    learner_name = models.CharField(max_length=255)
    course_title = models.CharField(max_length=220)
    grade = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    issued_at = models.DateTimeField(auto_now_add=True)


class NamedCategory(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=120, unique=True)
    position = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True
        ordering = ['position', 'name']

    def __str__(self):
        return self.name


class AcademyResourceCategory(NamedCategory):
    pass


class AcademyResource(models.Model):
    category = models.ForeignKey(AcademyResourceCategory, null=True, blank=True, on_delete=models.SET_NULL, related_name='resources')
    slug = models.SlugField(max_length=140, unique=True)
    title = models.CharField(max_length=220)
    description = models.TextField(blank=True)
    resource_file = models.FileField(upload_to='academy/resources/', null=True, blank=True)
    external_url = models.URLField(blank=True)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class DiagnosticCategory(NamedCategory):
    pass


class Diagnostic(models.Model):
    slug = models.SlugField(max_length=120, unique=True)
    title = models.CharField(max_length=220)
    version = models.PositiveIntegerField(default=1)
    is_published = models.BooleanField(default=False)


class DiagnosticQuestion(models.Model):
    diagnostic = models.ForeignKey(Diagnostic, on_delete=models.CASCADE, related_name='questions')
    category = models.ForeignKey(DiagnosticCategory, on_delete=models.PROTECT, related_name='questions')
    prompt = models.TextField()
    position = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['position', 'id']


class DiagnosticOption(models.Model):
    question = models.ForeignKey(DiagnosticQuestion, on_delete=models.CASCADE, related_name='options')
    label = models.CharField(max_length=255)
    score = models.PositiveSmallIntegerField()
    position = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['position', 'id']


class DiagnosticRecommendation(models.Model):
    diagnostic = models.ForeignKey(Diagnostic, on_delete=models.CASCADE, related_name='recommendation_rules')
    category = models.ForeignKey(DiagnosticCategory, null=True, blank=True, on_delete=models.CASCADE, related_name='recommendation_rules')
    course = models.ForeignKey(Course, on_delete=models.PROTECT, related_name='diagnostic_recommendations')
    minimum_score = models.PositiveSmallIntegerField(default=0, validators=[MaxValueValidator(100)])
    maximum_score = models.PositiveSmallIntegerField(default=100, validators=[MaxValueValidator(100)])
    message = models.CharField(max_length=255, blank=True)
    position = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['position', 'id']

    def clean(self):
        super().clean()
        if self.maximum_score < self.minimum_score:
            raise ValidationError({'maximum_score': 'Maximum score must be at least the minimum score.'})


class DiagnosticSubmission(CompanyOwnedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='diagnostic_submissions')
    diagnostic = models.ForeignKey(Diagnostic, on_delete=models.PROTECT, related_name='submissions')
    diagnostic_version = models.PositiveIntegerField()
    answers = models.JSONField(default=dict)
    category_scores = models.JSONField(default=dict)
    recommendations = models.JSONField(default=list)
    total_score = models.DecimalField(max_digits=5, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)


class OpportunityCategory(NamedCategory):
    pass


class FundingOpportunity(models.Model):
    category = models.ForeignKey(OpportunityCategory, null=True, blank=True, on_delete=models.SET_NULL, related_name='opportunities')
    slug = models.SlugField(max_length=140, unique=True)
    title = models.CharField(max_length=220)
    provider = models.CharField(max_length=220)
    description = models.TextField(blank=True)
    eligibility = models.TextField(blank=True)
    opens_on = models.DateField(null=True, blank=True)
    closes_on = models.DateField(null=True, blank=True)
    application_url = models.URLField(blank=True)
    contact_email = models.EmailField(blank=True)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class EventCategory(NamedCategory):
    pass


class AcademyEvent(models.Model):
    category = models.ForeignKey(EventCategory, null=True, blank=True, on_delete=models.SET_NULL, related_name='events')
    slug = models.SlugField(max_length=140, unique=True)
    title = models.CharField(max_length=220)
    description = models.TextField(blank=True)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField(null=True, blank=True)
    capacity = models.PositiveIntegerField(null=True, blank=True)
    venue = models.CharField(max_length=255, blank=True)
    meeting_url = models.URLField(blank=True)
    registration_url = models.URLField(blank=True)
    is_published = models.BooleanField(default=False)


class EventRegistration(CompanyOwnedModel):
    event = models.ForeignKey(AcademyEvent, on_delete=models.CASCADE, related_name='registrations')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='academy_event_registrations')
    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['company', 'event', 'user'], name='academy_unique_event_registration')]


class MentorProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mentor_profile')
    expertise = models.CharField(max_length=255)
    industries = models.CharField(max_length=255, blank=True)
    biography = models.TextField(blank=True)
    availability = models.TextField(blank=True)
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return self.user.get_full_name() or self.user.username


class MentorshipBooking(CompanyOwnedModel):
    class Status(models.TextChoices):
        REQUESTED = 'requested', 'Requested'
        ACCEPTED = 'accepted', 'Accepted'
        DECLINED = 'declined', 'Declined'
        COMPLETED = 'completed', 'Completed'

    learner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mentorship_bookings')
    mentor = models.ForeignKey(MentorProfile, on_delete=models.PROTECT, related_name='bookings')
    topic = models.TextField()
    requested_for = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.REQUESTED)
    created_at = models.DateTimeField(auto_now_add=True)


class Conversation(CompanyOwnedModel):
    booking = models.OneToOneField(MentorshipBooking, on_delete=models.CASCADE, related_name='conversation')
    created_at = models.DateTimeField(auto_now_add=True)

    def has_participant(self, user):
        return user.pk in {self.booking.learner_id, self.booking.mentor.user_id}


class ChatMessage(CompanyOwnedModel):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='academy_chat_messages')
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['created_at', 'id']


class ForumCategory(NamedCategory):
    pass


class ForumPost(CompanyOwnedModel):
    class Status(models.TextChoices):
        PUBLISHED = 'published', 'Published'
        HIDDEN = 'hidden', 'Hidden'

    category = models.ForeignKey(ForumCategory, null=True, blank=True, on_delete=models.SET_NULL, related_name='posts')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='forum_posts')
    title = models.CharField(max_length=220)
    body = models.TextField()
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PUBLISHED)
    is_pinned = models.BooleanField(default=False)
    is_locked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_pinned', '-created_at']


class ForumReply(CompanyOwnedModel):
    post = models.ForeignKey(ForumPost, on_delete=models.CASCADE, related_name='replies')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='forum_replies')
    body = models.TextField()
    is_hidden = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at', 'id']
