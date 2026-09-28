import hashlib
import json

from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.marketing.models import OutboundMessage, ProviderWebhookEvent


STATUS_ORDER = {"accepted": 1, "sent": 2, "delivered": 3, "read": 4}
TERMINAL = {"delivered", "read", "failed", "cancelled"}


def bounded_payload(payload, raw_body):
    serialized = json.dumps(payload, separators=(",", ":"), default=str)
    if len(serialized.encode("utf-8")) <= 16 * 1024:
        return payload
    return {"truncated": True, "sha256": hashlib.sha256(raw_body).hexdigest(), "bytes": len(raw_body)}


def event_digest(provider, event_id, event_type):
    return hashlib.sha256(f"{provider}:{event_id}:{event_type}".encode()).hexdigest()


def record_event(*, provider, event_id, event_type, payload, raw_body, message=None):
    stable_id = event_id or event_digest(provider, hashlib.sha256(raw_body).hexdigest(), event_type)
    try:
        with transaction.atomic():
            event = ProviderWebhookEvent.objects.create(
                provider=provider, event_id=stable_id, event_type=event_type,
                payload=bounded_payload(payload, raw_body), message=message,
            )
    except IntegrityError:
        return None
    return event


def apply_delivery_status(message, new_status):
    normalized = "failed" if new_status == "undelivered" else new_status
    current = message.status
    if current in TERMINAL:
        if current in {"delivered", "read"} and STATUS_ORDER.get(normalized, 0) > STATUS_ORDER.get(current, 0):
            pass
        else:
            return message
    elif normalized not in STATUS_ORDER and normalized != "failed":
        return message
    elif normalized != "failed" and STATUS_ORDER.get(normalized, 0) < STATUS_ORDER.get(current, 0):
        return message
    updates = {"status": normalized, "updated_at": timezone.now()}
    timestamp_field = {"sent": "sent_at", "delivered": "delivered_at", "read": "read_at", "failed": "failed_at"}.get(normalized)
    if timestamp_field:
        updates[timestamp_field] = timezone.now()
    OutboundMessage.objects.filter(pk=message.pk).update(**updates)
    message.refresh_from_db()
    return message
