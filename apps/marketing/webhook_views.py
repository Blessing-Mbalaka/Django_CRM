import json

from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST

from functionalities.marketing.providers.meta_common import validate_meta_signature
from functionalities.marketing.providers.twilio_sms import validate_twilio_request
from functionalities.marketing.webhooks import apply_delivery_status, record_event

from .models import OutboundMessage
from apps.companies.tenancy import company_context


def find_provider_message(request, provider, provider_id):
    if not provider_id:
        return None
    candidates = OutboundMessage.all_companies.filter(
        provider=provider, provider_message_id=provider_id, company__is_active=True,
    )
    if request.GET.get('company'):
        candidates = candidates.filter(company__slug=request.GET['company'])
    matches = list(candidates[:2])
    return matches[0] if len(matches) == 1 else None


@csrf_exempt
@require_POST
def twilio_status_webhook(request):
    params = request.POST.dict()
    if not validate_twilio_request(
        url=request.build_absolute_uri(), params=params,
        signature=request.headers.get("X-Twilio-Signature", ""),
    ):
        return HttpResponseForbidden()
    provider_id = params.get("MessageSid", "")
    status = params.get("MessageStatus", "").lower()
    message = find_provider_message(request, "twilio_sms", provider_id)
    with company_context(message.company_id if message else request.company.pk):
        event = record_event(
            provider="twilio_sms", event_id=f"{provider_id}:{status}", event_type=status,
            payload=params, raw_body=json.dumps(params, sort_keys=True).encode("utf-8"), message=message,
        )
        if event and message:
            apply_delivery_status(message, status)
            event.processed_at = event.received_at
            event.save(update_fields=["processed_at"])
    return HttpResponse(status=204)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def meta_webhook(request):
    if request.method == "GET":
        if (
            request.GET.get("hub.mode") == "subscribe"
            and request.GET.get("hub.verify_token") == settings.META_WEBHOOK_VERIFY_TOKEN
        ):
            return HttpResponse(request.GET.get("hub.challenge", ""), content_type="text/plain")
        return HttpResponseForbidden()
    if not validate_meta_signature(
        raw_body=request.body, signature_header=request.headers.get("X-Hub-Signature-256", "")
    ):
        return HttpResponseForbidden()
    try:
        payload = json.loads(request.body)
    except (TypeError, ValueError):
        return HttpResponse(status=400)
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            for status_item in change.get("value", {}).get("statuses", []):
                provider_id = str(status_item.get("id", ""))
                status = str(status_item.get("status", "")).lower()
                timestamp = str(status_item.get("timestamp", ""))
                message = find_provider_message(request, "meta_whatsapp", provider_id)
                with company_context(message.company_id if message else request.company.pk):
                    event = record_event(
                        provider="meta_whatsapp", event_id=f"{provider_id}:{status}:{timestamp}", event_type=status,
                        payload=status_item, raw_body=request.body, message=message,
                    )
                    if event and message:
                        apply_delivery_status(message, status)
                        event.processed_at = event.received_at
                        event.save(update_fields=["processed_at"])
    return HttpResponse(status=204)
