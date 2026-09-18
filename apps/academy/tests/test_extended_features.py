from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from apps.accounts.models import User
from apps.academy.funding_import import import_funding_csv
from apps.academy.models import (
    AcademyEvent, AcademyResource, AcademyResourceCategory, ChatMessage,
    Conversation, Diagnostic, DiagnosticCategory, DiagnosticOption,
    DiagnosticQuestion, EventCategory, EventRegistration, ForumCategory,
    ForumPost, FundingOpportunity, MentorProfile, MentorshipBooking,
    OpportunityCategory, Course, LearningPath, DiagnosticRecommendation,
)
from apps.academy.services import score_diagnostic


class AcademyExtendedFeatureTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='member', password='test-pass-123')
        self.mentor_user = User.objects.create_user(username='mentor', password='test-pass-123')

    def test_diagnostic_score_uses_admin_configured_options(self):
        diagnostic = Diagnostic.objects.create(slug='readiness', title='Readiness', is_published=True)
        category = DiagnosticCategory.objects.create(name='Finance', slug='finance')
        question = DiagnosticQuestion.objects.create(
            diagnostic=diagnostic, category=category, prompt='How ready?', position=1
        )
        low = DiagnosticOption.objects.create(question=question, label='Low', score=25, position=1)
        high = DiagnosticOption.objects.create(question=question, label='High', score=100, position=2)

        result = score_diagnostic(self.user, diagnostic, {str(question.id): high.id})

        self.assertEqual(result.total_score, 100)
        self.assertEqual(result.answers[str(question.id)], high.id)
        self.assertNotEqual(low.id, high.id)

    def test_diagnostic_stores_admin_configured_course_recommendations(self):
        path = LearningPath.objects.create(slug='build', title='Build', business_stage='build')
        course = Course.objects.create(
            path=path, slug='finance-basics', title='Finance basics', description='Learn.',
            instructor_name='Coach', duration_minutes=30,
        )
        diagnostic = Diagnostic.objects.create(slug='readiness', title='Readiness', is_published=True)
        category = DiagnosticCategory.objects.create(name='Finance', slug='finance')
        question = DiagnosticQuestion.objects.create(diagnostic=diagnostic, category=category, prompt='Ready?')
        option = DiagnosticOption.objects.create(question=question, label='Not yet', score=25)
        DiagnosticRecommendation.objects.create(
            diagnostic=diagnostic, category=category, course=course,
            minimum_score=0, maximum_score=50, message='Build your finance foundation.',
        )

        result = score_diagnostic(self.user, diagnostic, {str(question.id): option.id})

        self.assertEqual(result.recommendations[0]['course_slug'], 'finance-basics')

    def test_funding_csv_is_atomic_when_any_row_is_invalid(self):
        OpportunityCategory.objects.create(name='Grant', slug='grant')
        content = (
            'slug,title,provider,category,description,eligibility,opens_on,closes_on,application_url,contact_email,is_published\n'
            'valid,Valid Fund,Provider,grant,Description,Eligibility,2026-01-01,2026-12-31,https://example.com/apply,help@example.com,true\n'
            'invalid,Invalid Fund,Provider,missing,Description,Eligibility,2026-01-01,2026-12-31,https://example.com/apply,help@example.com,true\n'
        )
        upload = SimpleUploadedFile('funding.csv', content.encode(), content_type='text/csv')

        result = import_funding_csv(upload, commit=True)

        self.assertFalse(result.is_valid)
        self.assertEqual(FundingOpportunity.objects.count(), 0)
        self.assertEqual(result.errors[0]['row'], 3)

    def test_funding_csv_rejects_invalid_urls_and_dates(self):
        content = (
            'slug,title,provider,category,description,eligibility,opens_on,closes_on,application_url,contact_email,is_published\n'
            'invalid,Invalid Fund,Provider,,,2026-12-31,2026-01-01,not-a-url,not-an-email,true\n'
        )
        upload = SimpleUploadedFile('funding.csv', content.encode(), content_type='text/csv')

        result = import_funding_csv(upload, commit=True)

        self.assertFalse(result.is_valid)
        self.assertEqual(FundingOpportunity.objects.count(), 0)

    def test_event_registration_is_unique_per_user(self):
        category = EventCategory.objects.create(name='Webinar', slug='webinar')
        event = AcademyEvent.objects.create(
            category=category, slug='cashflow', title='Cash flow', starts_at='2026-10-01T08:00:00Z',
            registration_url='https://example.com/register', is_published=True,
        )
        EventRegistration.objects.create(event=event, user=self.user)
        with self.assertRaises(Exception):
            EventRegistration.objects.create(event=event, user=self.user)

    def test_messages_are_bound_to_conversation_participants(self):
        mentor = MentorProfile.objects.create(user=self.mentor_user, expertise='Finance', is_active=True)
        booking = MentorshipBooking.objects.create(learner=self.user, mentor=mentor, topic='Cash flow')
        conversation = Conversation.objects.create(booking=booking)
        message = ChatMessage.objects.create(conversation=conversation, sender=self.user, body='Hello')
        self.assertTrue(conversation.has_participant(self.user))
        self.assertTrue(conversation.has_participant(self.mentor_user))
        self.assertEqual(message.sender, self.user)

    def test_resource_and_forum_categories_are_admin_records(self):
        resource_category = AcademyResourceCategory.objects.create(name='Templates', slug='templates')
        resource = AcademyResource.objects.create(
            category=resource_category, slug='cash-flow', title='Cash Flow', is_published=True
        )
        forum_category = ForumCategory.objects.create(name='Finance', slug='finance')
        post = ForumPost.objects.create(category=forum_category, author=self.user, title='Question', body='Help')
        self.assertEqual(resource.category.name, 'Templates')
        self.assertEqual(post.author, self.user)
