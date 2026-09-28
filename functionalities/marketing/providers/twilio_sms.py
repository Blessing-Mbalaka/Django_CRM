import re

from django.conf import settings
from twilio.request_validator import RequestValidator
from twilio.rest import Client

from .base import ProviderError, ProviderResult


E164_PATTERN = re.compile(r"^\+[1-9]\d{7,14}$")


def _normalized_status(status):
    status = (status or "accepted").lower()
    if status in {"queued", "accepted", "scheduled"}:
        return "accepted"
    if status in {"sending", "sent"}:
        return "sent"
    if status in {"delivered", "read", "failed", "undelivered"}:
        return "failed" if status == "undelivered" else status
    return "accepted"


def send_sms(message):
    if not E164_PATTERN.fullmatch(message.destination or ""):
        raise ProviderError("SMS destination must use E.164 format.", retryable=False)
    required = (settings.TWILIO_ACCOUNT_SID, settings.TWILIO_API_KEY, settings.TWILIO_API_SECRET)
    if not all(required):
        raise ProviderError("Twilio SMS is not configured.", retryable=False)
    sender_number = settings.TWILIO_SMS_FROM_NUMBER
    messaging_service = settings.TWILIO_MESSAGING_SERVICE_SID
    if not sender_number and not messaging_service:
        raise ProviderError("Twilio SMS has no configured sender.", retryable=False)

    kwargs = {
        "to": message.destination,
        "body": message.content_snapshot,
        "status_callback": settings.TWILIO_STATUS_CALLBACK_URL,
    }
    if messaging_service:
        kwargs["messaging_service_sid"] = messaging_service
    else:
        kwargs["from_"] = sender_number
    try:
        client = Client(settings.TWILIO_API_KEY, settings.TWILIO_API_SECRET, account_sid=settings.TWILIO_ACCOUNT_SID)
        response = client.messages.create(**kwargs)
    except Exception as exc:
        status_code = getattr(exc, "status", None)
        code = getattr(exc, "code", None)
        retryable = status_code == 429 or bool(status_code and status_code >= 500)
        raise ProviderError(
            "Twilio SMS rejected the request." if not retryable else "Twilio SMS is temporarily unavailable.",
            retryable=retryable,
            status_code=status_code,
            safe_details={"provider_code": code} if code is not None else {},
        ) from exc
    return ProviderResult(
        str(response.sid),
        _normalized_status(getattr(response, "status", "accepted")),
        {"provider_status": getattr(response, "status", "")},
        retryable=False,
    )


def validate_twilio_request(*, url, params, signature):
    if not settings.TWILIO_AUTH_TOKEN or not signature:
        return False
    return RequestValidator(settings.TWILIO_AUTH_TOKEN).validate(url, params, signature)
