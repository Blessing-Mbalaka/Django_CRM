from decimal import Decimal

from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from .models import PayRun, PayrollEmployee, Payslip


class PayrollApiTests(APITestCase):
    def setUp(self):
        self.ceo = User.objects.create_user(
            username='payroll-ceo', password='test-pass-123', role=User.Role.CEO
        )
        self.staff = User.objects.create_user(
            username='payroll-staff', first_name='Pat', last_name='Employee',
            password='test-pass-123', role=User.Role.STAFF,
        )
        self.client.force_authenticate(self.ceo)

    def create_employee(self):
        response = self.client.post('/api/v1/payroll-employees/', {
            'user': self.staff.id,
            'employee_number': 'EMP-001',
            'tax_number': '1234567890',
            'monthly_basic': '30000.00',
            'is_active': True,
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response.data

    def test_ceo_can_complete_controlled_pay_run(self):
        employee = self.create_employee()
        response = self.client.post('/api/v1/pay-runs/', {
            'period_start': '2026-08-01',
            'period_end': '2026-08-31',
            'payment_date': '2026-08-31',
            'initial_payslip': {
                'employee': employee['id'],
                'basic_salary': '30000.00',
                'overtime': '1000.00',
                'allowances': '500.00',
                'paye': '5000.00',
                'uif_employee': '177.12',
                'uif_employer': '177.12',
                'other_deductions': '250.00',
            },
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Decimal(response.data['gross_total']), Decimal('31500.00'))
        self.assertEqual(Decimal(response.data['net_total']), Decimal('26072.88'))

        run_id = response.data['id']
        approved = self.client.post(f'/api/v1/pay-runs/{run_id}/approve/', {}, format='json')
        self.assertEqual(approved.status_code, status.HTTP_200_OK)
        self.assertEqual(approved.data['status'], PayRun.Status.APPROVED)
        self.assertEqual(approved.data['approved_by'], self.ceo.id)

        slip_id = approved.data['payslips'][0]['id']
        locked = self.client.patch(
            f'/api/v1/payslips/{slip_id}/', {'overtime': '2000.00'}, format='json'
        )
        self.assertEqual(locked.status_code, status.HTTP_400_BAD_REQUEST)

        paid = self.client.post(f'/api/v1/pay-runs/{run_id}/mark-paid/', {}, format='json')
        self.assertEqual(paid.status_code, status.HTTP_200_OK)
        self.assertEqual(paid.data['status'], PayRun.Status.PAID)

    def test_deductions_cannot_exceed_gross_pay(self):
        employee = self.create_employee()
        response = self.client.post('/api/v1/pay-runs/', {
            'period_start': '2026-09-01',
            'period_end': '2026-09-30',
            'payment_date': '2026-09-30',
            'initial_payslip': {
                'employee': employee['id'], 'basic_salary': '100.00',
                'paye': '101.00',
            },
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(PayRun.objects.exists())
        self.assertFalse(Payslip.objects.exists())

    def test_non_executive_cannot_access_payroll(self):
        director = User.objects.create_user(
            username='payroll-director', password='test-pass-123', role=User.Role.DIRECTOR
        )
        self.client.force_authenticate(director)
        self.assertEqual(self.client.get('/api/v1/pay-runs/').status_code, status.HTTP_403_FORBIDDEN)
        self.client.force_authenticate(user=None)
        self.client.force_login(director)
        response = self.client.get('/payroll/')
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response.url, '/')

    def test_payroll_page_and_navigation_are_available_to_ceo(self):
        self.client.force_login(self.ceo)
        response = self.client.get('/payroll/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, 'Payroll Management')
        self.assertContains(response, 'PAYE and UIF values are captured manually')
        self.assertContains(response, 'payrollEmployeeForm')
        dashboard = self.client.get('/')
        self.assertRedirects(dashboard, '/academy/', fetch_redirect_response=False)
        academy = self.client.get('/academy/')
        self.assertContains(academy, '/payroll/')


class PayrollModelTests(APITestCase):
    def test_employee_number_and_pay_period_are_unique(self):
        ceo = User.objects.create_user(username='model-ceo', role=User.Role.CEO)
        staff = User.objects.create_user(username='model-staff')
        PayrollEmployee.objects.create(
            user=staff, employee_number='EMP-U1', monthly_basic=Decimal('1.00')
        )
        PayRun.objects.create(
            period_start='2026-01-01', period_end='2026-01-31',
            payment_date='2026-01-31', created_by=ceo,
        )
        self.assertEqual(PayrollEmployee.objects.count(), 1)
        self.assertEqual(PayRun.objects.count(), 1)
