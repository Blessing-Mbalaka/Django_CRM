import hashlib
import hmac
import json

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from twilio.request_validator import RequestValidator

from apps.marketing.models import OutboundMessage, ProviderWebhookEvent


class MarketingWebhookTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="webhook-owner")
        self.message = OutboundMessage.objects.create(
            channel="sms", destination="+27728864770", content_snapshot="Hello",
            status="accepted", provider="twilio_sms", provider_message_id="SM123", created_by=self.user,
        )

    @override_settings(TWILIO_AUTH_TOKEN="auth-token")
    def test_twilio_signature_is_required_and_duplicate_status_is_idempotent(self):
        url = "http://testserver" + reverse("marketing:twilio-status-webhook")
        params = {"MessageSid": "SM123", "MessageStatus": "delivered"}
        signature = RequestValidator("auth-token").compute_signature(url, params)
        invalid = self.client.post(reverse("marketing:twilio-status-webhook"), params, HTTP_X_TWILIO_SIGNATURE="bad")
        self.assertEqual(invalid.status_code, 403)

        for _ in range(2):
            response = self.client.post(
                reverse("marketing:twilio-status-webhook"), params, HTTP_X_TWILIO_SIGNATURE=signature
            )
            self.assertEqual(response.status_code, 204)
        self.message.refresh_from_db()
        self.assertEqual(self.message.status, OutboundMessage.Status.DELIVERED)
        self.assertEqual(ProviderWebhookEvent.objects.filter(provider="twilio_sms").count(), 1)

    @override_settings(TWILIO_AUTH_TOKEN="auth-token")
    def test_unknown_twilio_id_is_recorded_without_failure_and_terminal_state_does_not_regress(self):
        path = reverse("marketing:twilio-status-webhook")
        url = "http://testserver" + path
        unknown = {"MessageSid": "UNKNOWN", "MessageStatus": "sent"}
        signature = RequestValidator("auth-token").compute_signature(url, unknown)
        self.assertEqual(self.client.post(path, unknown, HTTP_X_TWILIO_SIGNATURE=signature).status_code, 204)

        self.message.status = OutboundMessage.Status.DELIVERED
        self.message.save(update_fields=["status", "updated_at"])
        older = {"MessageSid": "SM123", "MessageStatus": "sent"}
        signature = RequestValidator("auth-token").compute_signature(url, older)
        self.client.post(path, older, HTTP_X_TWILIO_SIGNATURE=signature)
        self.message.refresh_from_db()
        self.assertEqual(self.message.status, OutboundMessage.Status.DELIVERED)

    @override_settings(META_WEBHOOK_VERIFY_TOKEN="verify-me")
    def test_meta_verification_challenge(self):
        response = self.client.get(
            reverse("marketing:meta-webhook"),
            {"hub.mode": "subscribe", "hub.verify_token": "verify-me", "hub.challenge": "challenge-123"},
        )
        self.assertEqual(response.content, b"challenge-123")
        denied = self.client.get(
            reverse("marketing:meta-webhook"),
            {"hub.mode": "subscribe", "hub.verify_token": "wrong", "hub.challenge": "x"},
        )
        self.assertEqual(denied.status_code, 403)

    @override_settings(META_APP_SECRET="app-secret")
    def test_meta_signature_idempotency_bounded_payload_and_monotonic_updates(self):
        self.message.channel = "whatsapp"
        self.message.provider = "meta_whatsapp"
        self.message.provider_message_id = "wamid.123"
        self.message.save(update_fields=["channel", "provider", "provider_message_id", "updated_at"])
        payload = {
            "entry": [{"changes": [{"value": {"statuses": [{
                "id": "wamid.123", "status": "read", "timestamp": "1700000000",
                "conversation": {"id": "x" * 20000},
            }]}}]}]
        }
        raw = json.dumps(payload).encode()
        signature = "sha256=" + hmac.new(b"app-secret", raw, hashlib.sha256).hexdigest()
        invalid = self.client.post(
            reverse("marketing:meta-webhook"), data=raw, content_type="application/json",
            HTTP_X_HUB_SIGNATURE_256="sha256=bad",
        )
        self.assertEqual(invalid.status_code, 403)
        for _ in range(2):
            response = self.client.post(
                reverse("marketing:meta-webhook"), data=raw, content_type="application/json",
                HTTP_X_HUB_SIGNATURE_256=signature,
            )
            self.assertEqual(response.status_code, 204)
        self.message.refresh_from_db()
        event = ProviderWebhookEvent.objects.get(provider="meta_whatsapp")
        self.assertEqual(self.message.status, OutboundMessage.Status.READ)
        self.assertLessEqual(len(json.dumps(event.payload)), 17000)
        self.assertEqual(ProviderWebhookEvent.objects.filter(provider="meta_whatsapp").count(), 1)
