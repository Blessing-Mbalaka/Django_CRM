from urllib.parse import quote

import requests
from django.conf import settings

from .base import ProviderError, ProviderResult


EMAIL_ENDPOINT = "https://comms.twilio.com/v1/Emails"
TIMEOUT = (5, 30)


def _auth():
    if not settings.TWILIO_EMAIL_API_KEY or not settings.TWILIO_EMAIL_API_SECRET:
        raise ProviderError("Twilio Email is not configured.", retryable=False)
    return settings.TWILIO_EMAIL_API_KEY, settings.TWILIO_EMAIL_API_SECRET


def _raise_for_response(response, *, operation="send"):
    status_code = response.status_code
    if status_code < 400:
        return
    retryable = status_code == 429 or status_code >= 500
    raise ProviderError(
        f"Twilio Email could not {operation} the message.",
        retryable=retryable,
        status_code=status_code,
        safe_details={"provider_status": status_code},
    )


def _json(response):
    try:
        return response.json()
    except (TypeError, ValueError) as exc:
        raise ProviderError("Twilio Email returned an unreadable response.", retryable=True) from exc


def send_email(message):
    payload = {
        "from": {
            "address": settings.TWILIO_EMAIL_FROM_ADDRESS,
            "name": settings.TWILIO_EMAIL_FROM_NAME,
        },
        "to": [{"address": message.destination}],
        "content": {
            "subject": message.subject_snapshot,
            "text": message.content_snapshot,
            "html": message.html_snapshot or message.content_snapshot,
        },
    }
    if getattr(message, "campaign_id", None):
        payload["tags"] = [{"name": "campaign", "value": str(message.campaign_id)}]
    if getattr(message, "scheduled_at", None):
        payload["send_at"] = message.scheduled_at.isoformat()
    try:
        response = requests.post(EMAIL_ENDPOINT, auth=_auth(), json=payload, timeout=TIMEOUT)
    except (requests.Timeout, requests.ConnectionError) as exc:
        raise ProviderError("Twilio Email is temporarily unreachable.", retryable=True) from exc
    except requests.RequestException as exc:
        raise ProviderError("Twilio Email request failed.", retryable=True) from exc
    _raise_for_response(response)
    if response.status_code != 202:
        raise ProviderError("Twilio Email returned an unexpected status.", retryable=True, status_code=response.status_code)
    data = _json(response)
    provider_id = str(data.get("id") or data.get("sid") or data.get("operation_id") or "")
    if not provider_id:
        raise ProviderError("Twilio Email did not return an operation identifier.", retryable=True)
    return ProviderResult(provider_id, "accepted", {"provider_status": response.status_code}, retryable=False)


def fetch_email_operation(operation_id):
    try:
        response = requests.get(f"{EMAIL_ENDPOINT}/{quote(operation_id, safe='')}", auth=_auth(), timeout=TIMEOUT)
    except (requests.Timeout, requests.ConnectionError) as exc:
        raise ProviderError("Twilio Email status is temporarily unreachable.", retryable=True) from exc
    except requests.RequestException as exc:
        raise ProviderError("Twilio Email status request failed.", retryable=True) from exc
    _raise_for_response(response, operation="read")
    data = _json(response)
    return ProviderResult(
        str(data.get("id") or operation_id),
        str(data.get("status") or "accepted").lower(),
        {"provider_status": response.status_code},
        retryable=False,
    )
