from apps.companies.tenancy import company_job
from django.core.management.base import BaseCommand, CommandError

from functionalities.marketing.scheduling import dispatch_due_marketing


class Command(BaseCommand):
    help = "Send due scheduled Marketing messages in a bounded batch."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=100)

    @company_job
    def handle(self, *args, **options):
        limit = options["limit"]
        if limit < 0:
            raise CommandError("--limit must be non-negative")
        summary = dispatch_due_marketing(limit=limit)
        self.stdout.write(
            f"selected={summary.selected} dispatched={summary.dispatched} failed={summary.failed}"
        )
