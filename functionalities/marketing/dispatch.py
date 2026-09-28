import re

from django.core.exceptions import PermissionDenied, ValidationError
from django.core.validators import validate_email
from django.db import transaction
from django.utils import timezone

from apps.marketing.models import DeliveryAttempt, OutboundMessage

from .providers.base import ProviderError
from .providers.meta_facebook import publish_facebook_post
from .providers.meta_instagram import publish_instagram_post
from .providers.meta_whatsapp import send_whatsapp
from .providers.twilio_email import send_email
from .providers.twilio_sms import send_sms


MAX_ATTEMPTS = 3
E164_PATTERN = re.compile(r"^\+[1-9]\d{7,14}$")
MANAGER_ROLES = {"dean", "director", "admin"}
PROVIDERS = {
    OutboundMessage.Channel.EMAIL: ("twilio_email", send_email),
    OutboundMessage.Channel.SMS: ("twilio_sms", send_sms),
    OutboundMessage.Channel.WHATSAPP: ("meta_whatsapp", send_whatsapp),
    OutboundMessage.Channel.FACEBOOK: ("meta_facebook", publish_facebook_post),
    OutboundMessage.Channel.INSTAGRAM: ("meta_instagram", publish_instagram_post),
}


def require_manager(actor):
    if not actor or not getattr(actor, "is_authenticated", False) or (
        not getattr(actor, "is_superuser", False) and getattr(actor, "role", "") not in MANAGER_ROLES
    ):
        raise PermissionDenied("Marketing management permission is required.")


def _validate_destination(message):
    if message.channel == OutboundMessage.Channel.EMAIL:
        try:
            validate_email(message.destination)
        except ValidationError as exc:
            raise ValidationError("Email destination is invalid.") from exc
    elif message.channel in {OutboundMessage.Channel.SMS, OutboundMessage.Channel.WHATSAPP}:
        if not E164_PATTERN.fullmatch(message.destination or ""):
            raise ValidationError("Mobile destination must use E.164 format.")
    if message.contact_id and message.channel in {
        OutboundMessage.Channel.EMAIL,
        OutboundMessage.Channel.SMS,
        OutboundMessage.Channel.WHATSAPP,
    }:
        message.contact.clean_for_channel(message.channel)


def queue_message(
    *, channel, actor, contact=None, campaign=None, content=None, destination="",
    subject="", body="", html="", media_url="", scheduled_at=None,
):
    require_manager(actor)
    if channel not in OutboundMessage.Channel.values:
        raise ValidationError("Unsupported marketing channel.")
    if contact:
        contact.clean_for_channel(channel)
        destination = contact.destination_for(channel)
    status = OutboundMessage.Status.SCHEDULED if scheduled_at else OutboundMessage.Status.DRAFT
    message = OutboundMessage(
        channel=channel,
        campaign=campaign,
        content=content,
        contact=contact,
        destination=destination,
        subject_snapshot=subject,
        content_snapshot=body,
        html_snapshot=html,
        media_url_snapshot=media_url,
        scheduled_at=scheduled_at,
        status=status,
        created_by=actor,
    )
    _validate_destination(message)
    message.full_clean()
    message.save()
    return message


def dispatch_message(message_id):
    with transaction.atomic():
        message = OutboundMessage.objects.select_for_update().select_related("contact").get(pk=message_id)
        now = timezone.now()
        claimable = message.status == OutboundMessage.Status.DRAFT or (
            message.status == OutboundMessage.Status.SCHEDULED
            and (message.scheduled_at is None or message.scheduled_at <= now)
        )
        if not claimable:
            return message
        if message.attempt_count >= MAX_ATTEMPTS:
            return message
        try:
            _validate_destination(message)
        except ValidationError:
            OutboundMessage.objects.filter(pk=message.pk).update(
                status=OutboundMessage.Status.FAILED,
                failed_at=now,
                last_error="Destination or consent validation failed.",
                updated_at=now,
            )
            return OutboundMessage.objects.get(pk=message.pk)
        updated = OutboundMessage.objects.filter(pk=message.pk, status=message.status).update(
            status=OutboundMessage.Status.PROCESSING,
            attempt_count=message.attempt_count + 1,
            updated_at=now,
        )
        if not updated:
            return OutboundMessage.objects.get(pk=message.pk)
        attempt = DeliveryAttempt.objects.create(
            message=message,
            attempt_number=message.attempt_count + 1,
        )

    provider_name, adapter = PROVIDERS[message.channel]
    try:
        message.refresh_from_db()
        result = adapter(message)
    except ProviderError as exc:
        with transaction.atomic():
            DeliveryAttempt.objects.filter(pk=attempt.pk).update(
                finished_at=timezone.now(), outcome="failed", http_status=exc.status_code,
                retryable=exc.retryable,
                error="Delivery provider temporarily failed." if exc.retryable else "Delivery provider rejected the message.",
                response_metadata=exc.safe_details,
            )
            OutboundMessage.objects.filter(pk=message.pk, status=OutboundMessage.Status.PROCESSING).update(
                status=OutboundMessage.Status.FAILED,
                provider=provider_name,
                failed_at=timezone.now(),
                last_error="Delivery provider temporarily failed." if exc.retryable else "Delivery provider rejected the message.",
                updated_at=timezone.now(),
            )
    except Exception:
        with transaction.atomic():
            DeliveryAttempt.objects.filter(pk=attempt.pk).update(
                finished_at=timezone.now(), outcome="failed", retryable=True,
                error="Unexpected delivery failure.", response_metadata={},
            )
            OutboundMessage.objects.filter(pk=message.pk, status=OutboundMessage.Status.PROCESSING).update(
                status=OutboundMessage.Status.FAILED, provider=provider_name,
                failed_at=timezone.now(), last_error="Unexpected delivery failure.", updated_at=timezone.now(),
            )
    else:
        normalized = result.status if result.status in OutboundMessage.Status.values else OutboundMessage.Status.ACCEPTED
        accepted_at = timezone.now() if normalized == OutboundMessage.Status.ACCEPTED else None
        sent_at = timezone.now() if normalized == OutboundMessage.Status.SENT else None
        with transaction.atomic():
            DeliveryAttempt.objects.filter(pk=attempt.pk).update(
                finished_at=timezone.now(), outcome=normalized, retryable=result.retryable,
                provider_status=normalized, response_metadata=result.metadata,
            )
            OutboundMessage.objects.filter(pk=message.pk, status=OutboundMessage.Status.PROCESSING).update(
                status=normalized, provider=provider_name, provider_message_id=result.provider_id,
                accepted_at=accepted_at, sent_at=sent_at, last_error="", updated_at=timezone.now(),
            )
    return OutboundMessage.objects.get(pk=message.pk)


def retry_message(*, message, actor):
    require_manager(actor)
    message.refresh_from_db()
    if message.status not in {OutboundMessage.Status.FAILED, OutboundMessage.Status.UNAVAILABLE}:
        raise ValidationError("Only failed or unavailable messages can be retried.")
    if message.attempt_count >= MAX_ATTEMPTS:
        raise ValidationError("Maximum delivery attempts reached.")
    latest = message.delivery_attempts.first()
    if latest and not latest.retryable:
        raise ValidationError("This delivery failure is not retryable.")
    OutboundMessage.objects.filter(pk=message.pk).update(
        status=OutboundMessage.Status.DRAFT, failed_at=None, last_error="", updated_at=timezone.now()
    )
    return OutboundMessage.objects.get(pk=message.pk)


def cancel_message(*, message, actor):
    require_manager(actor)
    message.refresh_from_db()
    if message.status not in {
        OutboundMessage.Status.DRAFT, OutboundMessage.Status.SCHEDULED,
        OutboundMessage.Status.FAILED, OutboundMessage.Status.UNAVAILABLE,
    }:
        raise ValidationError("This message can no longer be cancelled.")
    OutboundMessage.objects.filter(pk=message.pk).update(status=OutboundMessage.Status.CANCELLED, updated_at=timezone.now())
    return OutboundMessage.objects.get(pk=message.pk)
