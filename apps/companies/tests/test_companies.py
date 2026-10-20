from datetime import date
from io import StringIO
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from apps.companies.models import Company, CompanyOwnedModel
from apps.companies.storage import CompanyFileStorage
from apps.companies.tenancy import company_context, current_company_id
from apps.clients.models import Client
from apps.centres.models import Centre
from apps.products.models import Product
from apps.tasks.models import Board
from apps.inventory.models import InventorySettings, StockLocation
from apps.marketing.models import BrandKit, MarketingCampaign
from apps.academy.models import Course, CourseModule, CourseEnrollment, LearningPath, ModuleProgress


@override_settings(ALLOWED_HOSTS=['testserver'], EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class CompanyAccessTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.a = Company.objects.create(name='Alpha Company', slug='alpha')
        cls.b = Company.objects.create(name='Bravo Company', slug='bravo')
        cls.rows = {}
        for company, marker in ((cls.a, 'ALPHA-DATA'), (cls.b, 'BRAVO-SECRET')):
            with company_context(company):
                user = get_user_model().objects.create_user(username='owner', password='Review-Password-724!', first_name=marker, role='admin')
                user.email = 'owner@example.test'; user.save()
                centre = Centre.objects.create(name='Operations', code='OPS')
                client = Client.objects.create(name=marker, centre=centre)
                product = Product.objects.create(sku='SAME-SKU', name=marker)
                board = Board.objects.create(name=marker, owner=user)
                location = StockLocation.objects.create(name=marker, code='MAIN')
                campaign = MarketingCampaign.objects.create(name=marker, start_date=date(2026,1,1), end_date=date(2026,12,31), owner=user)
                from apps.purchasing.models import Supplier, PurchaseOrder
                from apps.sales.models import SalesOrder
                from apps.documents.models import DocumentLibrary, Document
                from apps.accounting.models import Account
                from apps.billing.models import Invoice
                from apps.payroll.models import PayrollEmployee, PayRun
                from apps.expenses.models import ExpenseCategory, Expense
                from apps.engagements.models import Engagement
                from apps.finance.models import FinancialRecord
                from apps.staff.models import StaffProfile
                from apps.alerts.models import Alert
                supplier = Supplier.objects.create(name=marker)
                library = DocumentLibrary.objects.create(name=marker, owner=user)
                expense_category = ExpenseCategory.objects.create(name='Travel')
                engagement = Engagement.objects.create(title=marker, client=client, centre=centre, lead_owner=user)
                extra = [
                    PurchaseOrder.objects.create(supplier=supplier, location=location, created_by=user, notes=marker),
                    SalesOrder.objects.create(client=client, created_by=user, notes=marker),
                    Document.objects.create(library=library, title=marker, owner=user),
                    Account.objects.create(code='1000', name=marker, account_type='asset', system_role='bank'),
                    Invoice.objects.create(client=client, created_by=user, due_date=date(2026,12,31)),
                    PayrollEmployee.objects.create(user=user, employee_number='EMP-1', monthly_basic=100),
                    PayRun.objects.create(period_start=date(2026,1,1), period_end=date(2026,1,31), payment_date=date(2026,1,31), created_by=user),
                    Expense.objects.create(category=expense_category, description=marker, amount=10, submitted_by=user),
                    FinancialRecord.objects.create(engagement=engagement, record_type='revenue', amount=10, date=date(2026,1,1)),
                    StaffProfile.objects.create(user=user, centre=centre),
                    Alert.objects.create(title=marker, alert_type='system', client=client),
                ]
                cls.rows[company.pk] = {'user':user, 'client':client, 'product':product, 'board':board,
                    'centre':centre, 'models':[centre, client, product, board, location, campaign, supplier, library, expense_category, engagement, *extra]}
        cls.path = LearningPath.objects.create(slug='shared', title='Shared learning', business_stage='foundations', is_published=True)
        cls.course = Course.objects.create(path=cls.path, slug='shared-course', title='Shared Course', position=1, duration_minutes=30, is_published=True)
        cls.module = CourseModule.objects.create(course=cls.course, title='Read this lesson', module_type='article', body='Shared lesson content', position=0, is_published=True)
        cls.quiz = CourseModule.objects.create(course=cls.course, title='Quiz', module_type='quiz', position=1, prompt='Choose the second answer', quiz_options=['Wrong','Correct'], correct_option=1, is_published=True)
        cls.activity = CourseModule.objects.create(course=cls.course, title='Reflection', module_type='reflection', position=2, prompt='Your next step?', is_published=True)

    def sign_in(self, company='alpha'):
        response = self.client.post('/accounts/login/', {'company':company, 'username':'owner', 'password':'Review-Password-724!'})
        self.assertEqual(response.status_code, 302, response.content[:200])

    def test_company_registration_creates_admin_with_no_platform_privileges(self):
        response = self.client.post('/accounts/register/', {'company_name':'New Workspace', 'company_code':'new-workspace',
            'username':'owner', 'email':'new@example.test', 'password1':'New-Workspace-Password-827!', 'password2':'New-Workspace-Password-827!'})
        self.assertEqual(response.status_code, 302)
        company = Company.objects.get(slug='new-workspace')
        owner = get_user_model().objects.get(company=company, username='owner')
        self.assertEqual(owner.role, 'admin')
        self.assertFalse(owner.is_superuser)
        self.assertFalse(owner.is_staff)
        self.assertEqual(self.client.get('/api/v1/products/').json()['count'], 0)
        self.assertEqual(self.client.get('/api/v1/academy/courses/').json()['count'], 1)

    def test_registration_rejects_duplicate_company_code_and_weak_password(self):
        response = self.client.post('/accounts/register/', {'company_name':'Duplicate', 'company_code':'ALPHA',
            'username':'other', 'email':'other@example.test', 'password1':'123', 'password2':'123'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'That company code is already in use.')
        self.assertEqual(Company.objects.filter(slug='alpha').count(), 1)

    def test_same_username_authenticates_in_the_selected_company(self):
        self.sign_in()
        self.assertContains(self.client.get('/api/v1/products/'), 'ALPHA-DATA')
        self.client.post('/accounts/logout/')
        self.sign_in('bravo')
        response = self.client.get('/api/v1/products/')
        self.assertContains(response, 'BRAVO-SECRET')
        self.assertNotContains(response, 'ALPHA-DATA')

    def test_wrong_company_password_and_missing_company_are_denied(self):
        other = self.rows[self.b.pk]['user']; other.set_password('Different-Password-836!'); other.save()
        for payload in ({'company':'bravo'}, {'company':'missing'}, {}):
            response = self.client.post('/accounts/login/', {**payload, 'username':'owner', 'password':'Review-Password-724!'})
            self.assertEqual(response.status_code, 200)
            self.assertNotIn('_auth_user_id', self.client.session)

    def test_every_business_domain_is_isolated(self):
        with company_context(self.a):
            for row in self.rows[self.b.pk]['models']:
                self.assertFalse(type(row).objects.filter(pk=row.pk).exists(), type(row).__name__)
        self.assertIsNone(current_company_id())

    def test_all_business_models_have_company_ownership(self):
        domains = {'accounts','centres','clients','staff','engagements','finance','alerts','communication','documents','tasks','billing','expenses','accounting','products','inventory','purchasing','sales','payroll','marketing'}
        for model in apps.get_models():
            if model._meta.app_label in domains:
                self.assertTrue(issubclass(model, CompanyOwnedModel), model._meta.label)

    def test_all_registered_api_lists_exclude_other_company(self):
        from apps.api.urls import router
        self.sign_in()
        for prefix, viewset, basename in router.registry:
            if not hasattr(viewset, 'list'): continue
            with self.subTest(route=prefix):
                response = self.client.get(f'/api/v1/{prefix}/')
                if 'manage' in prefix:
                    self.assertEqual(response.status_code, 403)
                else:
                    self.assertEqual(response.status_code, 200, response.content[:300])
                    self.assertNotIn(b'BRAVO-SECRET', response.content)

    def test_cross_company_read_update_delete_and_relationship_are_denied(self):
        self.sign_in()
        product = self.rows[self.b.pk]['product']
        for method in ('GET','PATCH','DELETE'):
            self.assertEqual(self.client.generic(method, f'/api/v1/products/{product.pk}/', data='{}', content_type='application/json').status_code, 404)
        response = self.client.post('/api/v1/invoices/', {'client':self.rows[self.b.pk]['client'].pk, 'due_date':'2026-12-31'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('client', response.json())

    def test_query_parameters_and_headers_do_not_switch_company(self):
        self.sign_in()
        response = self.client.get('/api/v1/products/?company=bravo', HTTP_X_COMPANY='bravo')
        self.assertContains(response, 'ALPHA-DATA')
        self.assertNotContains(response, 'BRAVO-SECRET')

    def test_create_assigns_company_and_duplicate_sku_returns_validation_error(self):
        self.sign_in()
        response = self.client.post('/api/v1/products/', {'name':'New', 'sku':'NEW', 'company':self.b.pk})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Product.all_companies.get(pk=response.json()['id']).company_id, self.a.pk)
        self.assertEqual(self.client.post('/api/v1/products/', {'name':'Duplicate','sku':'SAME-SKU'}).status_code, 400)

    def test_company_singletons_are_independent(self):
        for company in (self.a,self.b):
            with company_context(company):
                settings_row = InventorySettings.load(); settings_row.business_name=company.name; settings_row.save()
                brand = BrandKit.load(); brand.business_name=company.name; brand.save()
        with company_context(self.a):
            self.assertEqual(InventorySettings.load().business_name, self.a.name)
            self.assertEqual(BrandKit.load().business_name, self.a.name)

    def test_company_admin_can_add_users_without_granting_platform_access(self):
        self.sign_in()
        response = self.client.post('/accounts/team/', {'username':'employee','email':'employee@example.test','role':'staff',
            'password1':'Employee-Password-728!','password2':'Employee-Password-728!', 'company':self.b.pk, 'is_superuser':'on','is_staff':'on'})
        self.assertEqual(response.status_code,302)
        user = get_user_model().objects.get(username='employee')
        self.assertEqual(user.company_id,self.a.pk)
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_staff)
        self.assertNotContains(self.client.get('/accounts/team/'),'BRAVO-SECRET')

    def test_company_admin_cannot_change_shared_courses(self):
        self.sign_in()
        response = self.client.post('/api/v1/academy/manage/courses/', {'title':'Changed'})
        self.assertEqual(response.status_code,403)

    def test_lms_progress_persists_and_is_private_even_within_same_company(self):
        self.sign_in()
        enrollment = self.client.post('/api/v1/academy/courses/shared-course/enrol/').json()
        url = f"/api/v1/academy/enrollments/{enrollment['id']}/complete-module/"
        response = self.client.post(url, {'module':self.module.pk})
        self.assertEqual(response.status_code,200)
        self.assertEqual(len(response.json()['completed_modules']),1)
        self.assertEqual(len(self.client.get('/api/v1/academy/enrollments/').json()['results'][0]['completed_modules']),1)
        with company_context(self.a):
            coworker = get_user_model().objects.create_user('coworker',password='Coworker-Password-817!')
        self.client.force_login(coworker)
        self.assertEqual(self.client.get(f"/api/v1/academy/enrollments/{enrollment['id']}/").status_code,404)
        self.assertEqual(self.client.get('/api/v1/academy/enrollments/').json()['count'],0)
        self.client.post('/accounts/logout/'); self.sign_in('bravo')
        self.assertEqual(self.client.get('/api/v1/academy/courses/').json()['count'],1)
        self.assertEqual(self.client.get('/api/v1/academy/enrollments/').json()['count'],0)

    def test_quiz_grading_and_edited_reflections_are_saved_server_side(self):
        self.sign_in()
        enrollment = self.client.post('/api/v1/academy/courses/shared-course/enrol/').json()
        base=f"/api/v1/academy/enrollments/{enrollment['id']}/"
        self.assertFalse(self.client.post(base+'submit-quiz/', {'module':self.quiz.pk,'selected_option':0}).json()['is_correct'])
        self.assertTrue(self.client.post(base+'submit-quiz/', {'module':self.quiz.pk,'selected_option':1}).json()['is_correct'])
        for text in ('First response','Edited response'):
            self.assertEqual(self.client.post(base+'complete-module/', {'module':self.activity.pk,'response':text}).status_code,200)
        with company_context(self.a):
            progress=ModuleProgress.objects.get(enrollment_id=enrollment['id'],module=self.activity)
            self.assertEqual(progress.response,'Edited response')

    def test_files_are_company_owned_and_shared_course_resources_remain_available(self):
        from apps.academy.models import AcademyResource
        with TemporaryDirectory(dir=settings.BASE_DIR) as root, override_settings(MEDIA_ROOT=root):
            storage=CompanyFileStorage()
            with company_context(self.b):
                private=storage.save('private.txt',ContentFile(b'Bravo file'))
            with company_context(self.a):
                mine=storage.save('private.txt',ContentFile(b'Alpha file'))
            resource=AcademyResource.objects.create(slug='worksheet',title='Shared worksheet',is_published=True)
            resource.resource_file.save('worksheet.txt',ContentFile(b'Shared learning'))
            self.sign_in()
            self.assertEqual(self.client.get('/media/'+private).status_code,404)
            response=self.client.get('/media/'+mine)
            self.assertEqual(b''.join(response.streaming_content),b'Alpha file');response.close()
            response=self.client.get(resource.resource_file.url)
            self.assertEqual(b''.join(response.streaming_content),b'Shared learning');response.close()

    def test_forms_and_model_validation_reject_cross_company_relations(self):
        from apps.clients.forms import ClientForm
        from apps.engagements.models import Engagement
        with company_context(self.a):
            form=ClientForm(data={'name':'Forged','sector':'other','visibility':'shared','centre':self.rows[self.b.pk]['centre'].pk})
            self.assertFalse(form.is_valid())
            with self.assertRaises(ValidationError):
                Client.objects.create(name='Forged',centre=self.rows[self.b.pk]['centre'])
            engagement=Engagement.objects.create(title='Team',client=self.rows[self.a.pk]['client'])
            with self.assertRaises(ValidationError):
                engagement.team_members.add(self.rows[self.b.pk]['user'])

    def test_token_authentication_derives_company_from_token_user(self):
        token=Token.objects.create(user=self.rows[self.b.pk]['user'])
        client=APIClient()
        response=client.get('/api/v1/products/',HTTP_AUTHORIZATION=f'Token {token.key}',HTTP_X_COMPANY='alpha')
        self.assertContains(response,'BRAVO-SECRET')
        self.assertNotContains(response,'ALPHA-DATA')
        created=client.post('/api/v1/products/',{'sku':'TOKEN-WRITE','name':'Token product'},format='json',HTTP_AUTHORIZATION=f'Token {token.key}')
        self.assertEqual(created.status_code,201)
        self.assertEqual(Product.all_companies.get(pk=created.json()['id']).company_id,self.b.pk)

    def test_inactive_company_is_denied_but_can_sign_out(self):
        self.sign_in();self.a.is_active=False;self.a.save()
        self.assertEqual(self.client.get('/api/v1/products/').status_code,403)
        self.assertEqual(self.client.post('/accounts/logout/').status_code,302)

    def test_password_reset_uses_company_and_preserves_it_in_link(self):
        self.client.post('/accounts/password-reset/',{'company':'bravo','email':'owner@example.test'})
        self.assertEqual(len(mail.outbox),1)
        url=next(line for line in mail.outbox[0].body.splitlines() if line.startswith('http://'))
        self.assertIn('company=bravo',url)
        response=self.client.get(url)
        self.assertIn('company=bravo',response.url)
        self.assertEqual(self.client.post(response.url,{'new_password1':'Reset-Password-729!','new_password2':'Reset-Password-729!'}).status_code,302)
        self.rows[self.b.pk]['user'].refresh_from_db()
        self.assertTrue(self.rows[self.b.pk]['user'].check_password('Reset-Password-729!'))
        self.assertTrue(self.rows[self.a.pk]['user'].check_password('Review-Password-724!'))

    def test_background_jobs_are_explicitly_company_scoped(self):
        from apps.accounting.models import Account
        before=Account.all_companies.filter(company=self.b).count()
        call_command('company_command','alpha','bootstrap_accounts',stdout=StringIO())
        self.assertEqual(Account.all_companies.filter(company=self.b).count(),before)

    def test_external_login_redirect_is_rejected(self):
        response=self.client.post('/accounts/login/?next=https://example.org/',{'company':'alpha','username':'owner','password':'Review-Password-724!'})
        self.assertEqual(response.url,'/academy/')

    @override_settings(TWILIO_AUTH_TOKEN='test-provider-key')
    def test_signed_callback_updates_only_the_company_owning_the_message(self):
        from twilio.request_validator import RequestValidator
        from apps.marketing.models import OutboundMessage, ProviderWebhookEvent
        messages=[]
        for company in (self.a,self.b):
            with company_context(company):
                messages.append(OutboundMessage.objects.create(channel='sms',destination='+27721234567',content_snapshot='Hello',
                    status='accepted',provider='twilio_sms',provider_message_id=f'SM{company.pk}',created_by=self.rows[company.pk]['user']))
        path='/growth/webhooks/twilio/sms/'
        payload={'MessageSid':f'SM{self.b.pk}','MessageStatus':'delivered'}
        signature=RequestValidator('test-provider-key').compute_signature('http://testserver'+path,payload)
        self.assertEqual(self.client.post(path,payload,HTTP_X_TWILIO_SIGNATURE=signature).status_code,204)
        messages[0].refresh_from_db();messages[1].refresh_from_db()
        self.assertEqual(messages[0].status,'accepted')
        self.assertEqual(messages[1].status,'delivered')
        self.assertEqual(ProviderWebhookEvent.all_companies.get().company_id,self.b.pk)

    def test_scheduler_does_not_select_another_company_message(self):
        from django.utils import timezone
        from apps.marketing.models import OutboundMessage
        from functionalities.marketing.scheduling import dispatch_due_marketing
        messages=[]
        for company in (self.a,self.b):
            with company_context(company):
                messages.append(OutboundMessage.objects.create(channel='sms',destination='+27721234567',content_snapshot='Hello',
                    status='scheduled',scheduled_at=timezone.now(),created_by=self.rows[company.pk]['user']))
        with company_context(self.a), patch('functionalities.marketing.scheduling.dispatch_message',return_value=messages[0]) as send:
            self.assertEqual(dispatch_due_marketing(limit=10).selected,1)
            send.assert_called_once_with(messages[0].pk)
