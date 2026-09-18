from urllib.parse import urlencode

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

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


class Course(models.Model):
    class Level(models.TextChoices):
        BEGINNER = 'beginner', 'Beginner'
        INTERMEDIATE = 'intermediate', 'Intermediate'
        ADVANCED = 'advanced', 'Advanced'

    path = models.ForeignKey(LearningPath, on_delete=models.PROTECT, related_name='courses')
    slug = models.SlugField(max_length=120, unique=True)
    title = models.CharField(max_length=220)
    description = models.TextField()
    learning_outcome = models.CharField(max_length=255, blank=True)
    instructor_name = models.CharField(max_length=160)
    level = models.CharField(max_length=16, choices=Level.choices, default=Level.BEGINNER)
    duration_minutes = models.PositiveIntegerField(validators=[MinValueValidator(1)])
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

