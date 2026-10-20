import argparse
from django.core.management import BaseCommand, CommandError, call_command
from apps.companies.models import Company
from apps.companies.tenancy import company_context


class Command(BaseCommand):
    help = 'Run a business job for one active company.'

    def add_arguments(self, parser):
        parser.add_argument('company_code')
        parser.add_argument('command_name')
        parser.add_argument('command_args', nargs=argparse.REMAINDER)

    def handle(self, company_code, command_name, command_args, **options):
        allowed = {'send_due_marketing', 'bootstrap_accounts'}
        if command_name not in allowed:
            raise CommandError('Choose a supported business job: ' + ', '.join(sorted(allowed)))
        try:
            company = Company.objects.get(slug=company_code, is_active=True)
        except Company.DoesNotExist as exc:
            raise CommandError('Active company not found.') from exc
        with company_context(company):
            call_command(command_name, *command_args, stdout=self.stdout, stderr=self.stderr)
