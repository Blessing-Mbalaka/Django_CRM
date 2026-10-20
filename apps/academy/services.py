from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Prefetch
from django.utils import timezone

from .models import (
    Certificate, DiagnosticOption, DiagnosticQuestion, DiagnosticSubmission,
    ModuleProgress, QuizAttempt,
)


@transaction.atomic
def recalculate_enrollment(enrollment):
    required = enrollment.course.modules.filter(is_published=True, is_required=True)
    completed_ids = set(enrollment.module_progress.values_list('module_id', flat=True))
    all_complete = all(module.id in completed_ids for module in required)
    quiz_modules = list(required.filter(module_type='quiz'))
    scores = []
    for module in quiz_modules:
        attempt = enrollment.quiz_attempts.filter(module=module).order_by('-created_at', '-id').first()
        scores.append(attempt.score if attempt else Decimal('0'))
    grade = sum(scores, Decimal('0')) / len(scores) if scores else Decimal('100')
    enrollment.final_grade = grade
    if all_complete:
        enrollment.completed_at = enrollment.completed_at or timezone.now()
        enrollment.status = enrollment.Status.PASSED if grade >= enrollment.course.passing_grade else enrollment.Status.FAILED
        if enrollment.status == enrollment.Status.PASSED and enrollment.course.certificate_enabled:
            Certificate.objects.get_or_create(enrollment=enrollment, defaults={
                'learner_name': enrollment.user.get_full_name() or enrollment.user.username,
                'course_title': enrollment.course.title,
                'grade': grade,
            })
    else:
        enrollment.status = enrollment.Status.IN_PROGRESS if completed_ids or enrollment.quiz_attempts.exists() else enrollment.Status.NOT_STARTED
    enrollment.started_at = enrollment.started_at or (timezone.now() if enrollment.status != enrollment.Status.NOT_STARTED else None)
    enrollment.save(update_fields=['status', 'final_grade', 'started_at', 'completed_at', 'updated_at'])
    return enrollment


@transaction.atomic
def complete_module(enrollment, module, response=''):
    if module.course_id != enrollment.course_id or not module.is_published:
        raise ValidationError('Module does not belong to this published course.')
    if module.module_type == module.Type.QUIZ:
        raise ValidationError('Quiz modules are completed by a correct quiz submission.')
    ModuleProgress.objects.update_or_create(enrollment=enrollment, module=module, defaults={'response': response})
    return recalculate_enrollment(enrollment)


@transaction.atomic
def submit_quiz(enrollment, module, selected_option):
    if module.course_id != enrollment.course_id or module.module_type != module.Type.QUIZ or not module.is_published:
        raise ValidationError('Choose a quiz module from this course.')
    if selected_option < 0 or selected_option >= len(module.quiz_options):
        raise ValidationError('Choose a valid quiz option.')
    correct = selected_option == module.correct_option
    attempt = QuizAttempt.objects.create(
        enrollment=enrollment, module=module, selected_option=selected_option,
        is_correct=correct, score=Decimal('100') if correct else Decimal('0'),
    )
    ModuleProgress.objects.get_or_create(enrollment=enrollment, module=module)
    recalculate_enrollment(enrollment)
    return attempt


@transaction.atomic
def score_diagnostic(user, diagnostic, answers):
    active_options = DiagnosticOption.objects.filter(is_active=True).order_by('position', 'id')
    questions = list(
        diagnostic.questions.filter(is_active=True)
        .prefetch_related(None)
        .select_related('category')
        .prefetch_related(Prefetch('options', queryset=active_options))
    )
    category_values = {}
    stored = {}
    scores = []
    for question in questions:
        option_id = int(answers.get(str(question.id), 0))
        try:
            option = next(option for option in question.options.all() if option.id == option_id)
        except StopIteration as exc:
            raise ValidationError(f'Choose a valid answer for question {question.id}.') from exc
        stored[str(question.id)] = option.id
        scores.append(option.score)
        category_values.setdefault(question.category.slug, []).append(option.score)
    category_scores = {key: sum(values) / len(values) for key, values in category_values.items()}
    total = sum(scores) / len(scores) if scores else 0
    recommendations = []
    for rule in diagnostic.recommendation_rules.filter(is_active=True).select_related('category', 'course'):
        score = category_scores.get(rule.category.slug, total) if rule.category else total
        if rule.minimum_score <= score <= rule.maximum_score:
            recommendations.append({
                'course_slug': rule.course.slug,
                'course_title': rule.course.title,
                'message': rule.message,
            })
    return DiagnosticSubmission.objects.create(
        user=user, diagnostic=diagnostic, diagnostic_version=diagnostic.version,
        answers=stored, category_scores=category_scores, recommendations=recommendations,
        total_score=total,
    )
