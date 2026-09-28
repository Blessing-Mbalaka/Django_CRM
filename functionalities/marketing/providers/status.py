from dataclasses import dataclass
from enum import Enum

import requests
from django.conf import settings


class ProviderState(str, Enum):
    AVAILABLE = "available"
    NOT_CONFIGURED = "not_configured"
    UNAVAILABLE = "unavailable"
    TEMPORARILY_FAILING = "temporarily_failing"


@dataclass(frozen=True, slots=True)
class ProviderStatus:
    provider: str
    state: ProviderState
    message: str
    missing: tuple[str, ...] = ()


PROVIDER_REQUIREMENTS = {
    "twilio_email": ("TWILIO_EMAIL_API_KEY", "TWILIO_EMAIL_API_SECRET", "TWILIO_EMAIL_FROM_ADDRESS", "TWILIO_EMAIL_FROM_NAME"),
    "twilio_sms": ("TWILIO_ACCOUNT_SID", "TWILIO_API_KEY", "TWILIO_API_SECRET", "TWILIO_AUTH_TOKEN", "TWILIO_STATUS_CALLBACK_URL"),
    "meta_whatsapp": ("META_GRAPH_API_VERSION", "META_ACCESS_TOKEN", "META_APP_SECRET", "META_WEBHOOK_VERIFY_TOKEN", "META_WHATSAPP_PHONE_NUMBER_ID", "META_WHATSAPP_BUSINESS_ACCOUNT_ID"),
    "meta_facebook": ("META_GRAPH_API_VERSION", "META_APP_SECRET", "META_FACEBOOK_PAGE_ID", "META_FACEBOOK_PAGE_ACCESS_TOKEN"),
    "meta_instagram": ("META_GRAPH_API_VERSION", "META_APP_SECRET", "META_INSTAGRAM_USER_ID", "META_INSTAGRAM_ACCESS_TOKEN", "MARKETING_PUBLIC_BASE_URL"),
}


def _missing_for(provider):
    missing = [name for name in PROVIDER_REQUIREMENTS[provider] if not getattr(settings, name, "")]
    if provider == "twilio_sms" and not (
        getattr(settings, "TWILIO_SMS_FROM_NUMBER", "") or getattr(settings, "TWILIO_MESSAGING_SERVICE_SID", "")
    ):
        missing.append("TWILIO_SMS_FROM_NUMBER|TWILIO_MESSAGING_SERVICE_SID")
    return tuple(missing)


def _probe(provider):
    version = settings.META_GRAPH_API_VERSION
    if provider == "meta_whatsapp":
        resource_id, token = settings.META_WHATSAPP_PHONE_NUMBER_ID, settings.META_ACCESS_TOKEN
    elif provider == "meta_facebook":
        resource_id, token = settings.META_FACEBOOK_PAGE_ID, settings.META_FACEBOOK_PAGE_ACCESS_TOKEN
    elif provider == "meta_instagram":
        resource_id, token = settings.META_INSTAGRAM_USER_ID, settings.META_INSTAGRAM_ACCESS_TOKEN
    else:
        return
    response = requests.get(
        f"https://graph.facebook.com/{version}/{resource_id}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=(5, 15),
    )
    response.raise_for_status()


def provider_status(*, probe=False):
    statuses = {}
    for provider in PROVIDER_REQUIREMENTS:
        missing = _missing_for(provider)
        if missing:
            statuses[provider] = ProviderStatus(
                provider, ProviderState.NOT_CONFIGURED,
                "Not configured yet. Add the listed environment variables to enable this service.", missing,
            )
            continue
        if probe:
            try:
                _probe(provider)
            except Exception:
                statuses[provider] = ProviderStatus(
                    provider, ProviderState.TEMPORARILY_FAILING,
                    "Configured, but the provider is temporarily unavailable.",
                )
                continue
        statuses[provider] = ProviderStatus(provider, ProviderState.AVAILABLE, "Configured and available.")
    return statuses
