from apps.companies.tenancy import company_job
from dataclasses import dataclass
from datetime import timedelta

from django.db.models import Q
from django.utils import timezone

from apps.marketing.models import OutboundMessage

from .dispatch import dispatch_message


@dataclass(frozen=True, slots=True)
class DispatchSummary:
    selected: int = 0
    dispatched: int = 0
    failed: int = 0


@company_job
def dispatch_due_marketing(*, limit=100):
    if limit < 0:
        raise ValueError("limit must be non-negative")
    now = timezone.now()
    stale_before = now - timedelta(minutes=15)
    OutboundMessage.objects.filter(
        status=OutboundMessage.Status.PROCESSING,
        updated_at__lt=stale_before,
        scheduled_at__lte=now,
    ).update(status=OutboundMessage.Status.SCHEDULED, last_error="Recovered stale processing claim.")
    ids = list(
        OutboundMessage.objects.filter(status=OutboundMessage.Status.SCHEDULED, scheduled_at__lte=now)
        .order_by("scheduled_at", "pk")
        .values_list("pk", flat=True)[:limit]
    )
    dispatched = failed = 0
    for message_id in ids:
        try:
            message = dispatch_message(message_id)
        except Exception:
            failed += 1
            continue
        if message.status == OutboundMessage.Status.FAILED:
            failed += 1
        elif message.status not in {OutboundMessage.Status.SCHEDULED, OutboundMessage.Status.PROCESSING}:
            dispatched += 1
    return DispatchSummary(selected=len(ids), dispatched=dispatched, failed=failed)
