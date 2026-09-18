from django.contrib import admin

from .models import Course, CourseModule, LearningPath


@admin.register(LearningPath)
class LearningPathAdmin(admin.ModelAdmin):
    list_display = ('title', 'business_stage', 'position', 'is_published', 'updated_at')
    list_editable = ('position', 'is_published')
    list_filter = ('business_stage', 'is_published')
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}


class CourseModuleInline(admin.StackedInline):
    model = CourseModule
    extra = 0
    ordering = ('position',)
    fields = (
        'position',
        'title',
        'module_type',
        'body',
        'prompt',
        'video_url',
        'resource_url',
        'quiz_options',
        'correct_option',
        'is_published',
    )


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'path', 'level', 'duration_minutes', 'position', 'is_published', 'updated_at')
    list_editable = ('position', 'is_published')
    list_filter = ('path', 'level', 'is_published')
    search_fields = ('title', 'description', 'learning_outcome', 'instructor_name')
    prepopulated_fields = {'slug': ('title',)}
    autocomplete_fields = ('path',)
    inlines = (CourseModuleInline,)
