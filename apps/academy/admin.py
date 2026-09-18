import csv

from django import forms
from django.contrib import admin, messages
from django.http import HttpResponse
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import path, reverse

from .funding_import import FUNDING_CSV_HEADERS, import_funding_csv
from .models import (
    AcademyEvent, AcademyResource, AcademyResourceCategory, Certificate,
    ChatMessage, Conversation, Course, CourseCategory, CourseEnrollment,
    CourseLevel, CourseModule, Diagnostic, DiagnosticCategory,
    DiagnosticOption, DiagnosticQuestion, DiagnosticRecommendation, DiagnosticSubmission, EventCategory,
    EventRegistration, ForumCategory, ForumPost, ForumReply,
    FundingOpportunity, LearningPath, MentorProfile, MentorshipBooking,
    OpportunityCategory,
)


class NamedCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'position', 'is_active')
    list_editable = ('position', 'is_active')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


for category_model in (
    CourseCategory, CourseLevel, AcademyResourceCategory, DiagnosticCategory,
    OpportunityCategory, EventCategory, ForumCategory,
):
    admin.site.register(category_model, NamedCategoryAdmin)


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
        'position', 'title', 'module_type', 'body', 'prompt', 'video_url',
        'resource_url', 'quiz_options', 'correct_option', 'is_required',
        'is_published',
    )


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'path', 'category', 'level_config', 'duration_minutes',
        'passing_grade', 'position', 'is_published', 'updated_at',
    )
    list_editable = ('position', 'is_published')
    list_filter = ('path', 'category', 'level_config', 'is_published', 'certificate_enabled')
    search_fields = ('title', 'description', 'learning_outcome', 'instructor_name')
    prepopulated_fields = {'slug': ('title',)}
    autocomplete_fields = ('path',)
    inlines = (CourseModuleInline,)


@admin.register(CourseEnrollment)
class CourseEnrollmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'status', 'final_grade', 'started_at', 'completed_at')
    list_filter = ('status', 'course')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'course__title')
    readonly_fields = ('status', 'final_grade', 'started_at', 'completed_at', 'created_at', 'updated_at')


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('learner_name', 'course_title', 'grade', 'verification_id', 'issued_at')
    search_fields = ('learner_name', 'course_title', 'verification_id')
    readonly_fields = ('enrollment', 'verification_id', 'learner_name', 'course_title', 'grade', 'issued_at')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(AcademyResource)
class AcademyResourceAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'is_published', 'created_at')
    list_filter = ('category', 'is_published')
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}


class DiagnosticOptionInline(admin.TabularInline):
    model = DiagnosticOption
    extra = 2
    ordering = ('position',)


class DiagnosticRecommendationInline(admin.TabularInline):
    model = DiagnosticRecommendation
    extra = 0
    ordering = ('position',)


@admin.register(DiagnosticQuestion)
class DiagnosticQuestionAdmin(admin.ModelAdmin):
    list_display = ('prompt', 'diagnostic', 'category', 'position')
    list_filter = ('diagnostic', 'category')
    inlines = (DiagnosticOptionInline,)


@admin.register(Diagnostic)
class DiagnosticAdmin(admin.ModelAdmin):
    list_display = ('title', 'version', 'is_published')
    list_editable = ('is_published',)
    prepopulated_fields = {'slug': ('title',)}
    inlines = (DiagnosticRecommendationInline,)


@admin.register(DiagnosticSubmission)
class DiagnosticSubmissionAdmin(admin.ModelAdmin):
    list_display = ('user', 'diagnostic', 'diagnostic_version', 'total_score', 'created_at')
    list_filter = ('diagnostic', 'created_at')
    readonly_fields = ('user', 'diagnostic', 'diagnostic_version', 'answers', 'category_scores', 'recommendations', 'total_score', 'created_at')

    def has_add_permission(self, request):
        return False


class FundingCsvUploadForm(forms.Form):
    csv_file = forms.FileField(help_text='Upload the unmodified UTF-8 CSV template.')


@admin.register(FundingOpportunity)
class FundingOpportunityAdmin(admin.ModelAdmin):
    change_list_template = 'admin/academy/fundingopportunity/change_list.html'
    list_display = ('title', 'provider', 'category', 'opens_on', 'closes_on', 'is_published')
    list_filter = ('category', 'is_published', 'opens_on', 'closes_on')
    search_fields = ('title', 'provider', 'description', 'eligibility')
    prepopulated_fields = {'slug': ('title',)}

    def get_urls(self):
        custom = [
            path('import-csv/', self.admin_site.admin_view(self.import_csv), name='academy_fundingopportunity_import_csv'),
            path('csv-template/', self.admin_site.admin_view(self.csv_template), name='academy_fundingopportunity_csv_template'),
        ]
        return custom + super().get_urls()

    def csv_template(self, request):
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="funding-opportunities-template.csv"'
        writer = csv.writer(response)
        writer.writerow(FUNDING_CSV_HEADERS)
        writer.writerow([
            'example-grant', 'Example grant', 'Provider name', 'grant',
            'What the fund supports', 'Who can apply', '2026-01-01', '2026-12-31',
            'https://example.org/apply', 'fund@example.org', 'false',
        ])
        return response

    def import_csv(self, request):
        result = None
        form = FundingCsvUploadForm(request.POST or None, request.FILES or None)
        if request.method == 'POST' and form.is_valid():
            result = import_funding_csv(form.cleaned_data['csv_file'], commit=True)
            if result.is_valid:
                self.message_user(request, f'Imported {result.imported} funding opportunities.', messages.SUCCESS)
                return redirect(reverse('admin:academy_fundingopportunity_changelist'))
        context = {
            **self.admin_site.each_context(request),
            'title': 'Import funding opportunities',
            'opts': self.model._meta,
            'form': form,
            'result': result,
            'template_url': reverse('admin:academy_fundingopportunity_csv_template'),
        }
        return TemplateResponse(request, 'admin/academy/fundingopportunity/import_csv.html', context)


@admin.register(AcademyEvent)
class AcademyEventAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'starts_at', 'capacity', 'is_published')
    list_filter = ('category', 'is_published', 'starts_at')
    search_fields = ('title', 'description', 'venue')
    prepopulated_fields = {'slug': ('title',)}


@admin.register(EventRegistration)
class EventRegistrationAdmin(admin.ModelAdmin):
    list_display = ('event', 'user', 'registered_at')
    list_filter = ('event', 'registered_at')
    readonly_fields = ('registered_at',)


@admin.register(MentorProfile)
class MentorProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'expertise', 'industries', 'is_active')
    list_editable = ('is_active',)
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'expertise', 'industries')


@admin.register(MentorshipBooking)
class MentorshipBookingAdmin(admin.ModelAdmin):
    list_display = ('learner', 'mentor', 'requested_for', 'status', 'created_at')
    list_filter = ('status', 'mentor')
    search_fields = ('learner__username', 'mentor__user__username', 'topic')


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ('sender', 'body', 'created_at', 'read_at')

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('booking', 'created_at')
    inlines = (ChatMessageInline,)


class ForumReplyInline(admin.TabularInline):
    model = ForumReply
    extra = 0
    fields = ('author', 'body', 'is_hidden', 'created_at')
    readonly_fields = ('created_at',)


@admin.register(ForumPost)
class ForumPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'author', 'status', 'is_pinned', 'is_locked', 'created_at')
    list_filter = ('category', 'status', 'is_pinned', 'is_locked')
    search_fields = ('title', 'body', 'author__username')
    inlines = (ForumReplyInline,)
