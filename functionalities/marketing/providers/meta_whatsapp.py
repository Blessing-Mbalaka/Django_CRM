from django.conf import settings

from .base import ProviderError, ProviderResult
from .meta_common import post_graph


def send_whatsapp(message):
    if not message.destination:
        raise ProviderError("WhatsApp destination is required.", retryable=False)
    template_name = getattr(message, "template_name", "")
    if template_name:
        payload = {
            "messaging_product": "whatsapp",
            "to": message.destination,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": getattr(message, "template_language", "en_US")},
            },
        }
        components = getattr(message, "template_components", None)
        if components:
            payload["template"]["components"] = components
    elif message.content_snapshot:
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": message.destination,
            "type": "text",
            "text": {"preview_url": False, "body": message.content_snapshot},
        }
    else:
        raise ProviderError("WhatsApp content or an approved template is required.", retryable=False)

    data = post_graph(
        f"{settings.META_WHATSAPP_PHONE_NUMBER_ID}/messages",
        token=settings.META_ACCESS_TOKEN,
        payload=payload,
    )
    messages = data.get("messages") or []
    provider_id = messages[0].get("id") if messages else ""
    if not provider_id:
        raise ProviderError("Meta did not return a WhatsApp message identifier.", retryable=True)
    return ProviderResult(str(provider_id), "accepted", {"channel": "whatsapp"}, retryable=False)
