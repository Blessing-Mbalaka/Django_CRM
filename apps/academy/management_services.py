from dataclasses import dataclass

from .models import (
    AcademyEvent, AcademyResourceCategory, Course, CourseCategory, CourseLevel,
    CourseModule, Diagnostic, DiagnosticCategory, DiagnosticOption,
    DiagnosticQuestion, DiagnosticRecommendation, EventCategory, ForumCategory,
    ForumPost, LearningPath, MentorProfile, OpportunityCategory,
)


@dataclass(frozen=True)
class RemovalResult:
    action: str
    instance: object | None


def _archive(instance, field, value=False):
    setattr(instance, field, value)
    instance.save(update_fields=[field])
    return RemovalResult('archived', instance)


def _has_category_content(instance):
    relation_names = {
        CourseCategory: ('courses',),
        CourseLevel: ('courses',),
        AcademyResourceCategory: ('resources',),
        DiagnosticCategory: ('questions', 'recommendation_rules'),
        OpportunityCategory: ('opportunities',),
        EventCategory: ('events',),
        ForumCategory: ('posts',),
    }
    return any(getattr(instance, name).exists() for name in relation_names.get(type(instance), ()))


def safe_remove(instance):
    if isinstance(instance, (CourseCategory, CourseLevel, AcademyResourceCategory,
                            DiagnosticCategory, OpportunityCategory, EventCategory,
                            ForumCategory)) and _has_category_content(instance):
        return _archive(instance, 'is_active')
    if isinstance(instance, LearningPath) and instance.courses.exists():
        return _archive(instance, 'is_published')
    if isinstance(instance, Course) and (
        instance.enrollments.exists() or instance.diagnostic_recommendations.exists()
    ):
        return _archive(instance, 'is_published')
    if isinstance(instance, CourseModule) and (
        instance.learner_progress.exists() or instance.quiz_attempts.exists()
    ):
        return _archive(instance, 'is_published')
    if isinstance(instance, Diagnostic) and instance.submissions.exists():
        return _archive(instance, 'is_published')
    if isinstance(instance, DiagnosticQuestion) and instance.diagnostic.submissions.exists():
        return _archive(instance, 'is_active')
    if isinstance(instance, DiagnosticOption) and instance.question.diagnostic.submissions.exists():
        return _archive(instance, 'is_active')
    if isinstance(instance, DiagnosticRecommendation) and instance.diagnostic.submissions.exists():
        return _archive(instance, 'is_active')
    if isinstance(instance, AcademyEvent) and instance.registrations.exists():
        return _archive(instance, 'is_published')
    if isinstance(instance, MentorProfile) and instance.bookings.exists():
        return _archive(instance, 'is_active')
    if isinstance(instance, ForumPost):
        return _archive(instance, 'status', ForumPost.Status.HIDDEN)
    instance.delete()
    return RemovalResult('deleted', None)
