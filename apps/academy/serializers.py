from rest_framework import serializers

from .models import Course, CourseModule, LearningPath


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
        ]

    def get_video_embed_url(self, module):
        if not module.video_url:
            return ''
        request = self.context.get('request')
        origin = request.build_absolute_uri('/').rstrip('/') if request else ''
        return module.youtube_embed_url(origin)


class CourseListSerializer(serializers.ModelSerializer):
    path = LearningPathSummarySerializer(read_only=True)
    level_label = serializers.CharField(source='get_level_display', read_only=True)

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
            'duration_minutes',
            'position',
            'path',
        ]


class CourseDetailSerializer(CourseListSerializer):
    modules = serializers.SerializerMethodField()

    class Meta(CourseListSerializer.Meta):
        fields = CourseListSerializer.Meta.fields + ['modules']

    def get_modules(self, course):
        modules = getattr(course, 'published_modules', course.modules.filter(is_published=True))
        return CourseModuleSerializer(modules, many=True, context=self.context).data

