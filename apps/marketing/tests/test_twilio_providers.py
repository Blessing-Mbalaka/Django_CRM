from types import SimpleNamespace
from unittest.mock import Mock, patch

import requests
from django.test import SimpleTestCase, override_settings

from functionalities.marketing.providers.base import ProviderError
from functionalities.marketing.providers.twilio_email import fetch_email_operation, send_email
from functionalities.marketing.providers.twilio_sms import send_sms, validate_twilio_request


EMAIL_SETTINGS = {
    "TWILIO_EMAIL_API_KEY": "SK_email",
    "TWILIO_EMAIL_API_SECRET": "email-secret",
    "TWILIO_EMAIL_FROM_ADDRESS": "verified@example.test",
    "TWILIO_EMAIL_FROM_NAME": "Example Business",
}

SMS_SETTINGS = {
    "TWILIO_ACCOUNT_SID": "AC_account",
    "TWILIO_API_KEY": "SK_sms",
    "TWILIO_API_SECRET": "sms-secret",
    "TWILIO_AUTH_TOKEN": "auth-token",
    "TWILIO_SMS_FROM_NUMBER": "+17372508034",
    "TWILIO_MESSAGING_SERVICE_SID": "",
    "TWILIO_STATUS_CALLBACK_URL": "https://example.test/growth/webhooks/twilio/sms/",
}


def message(**overrides):
    values = {
        "destination": "recipient@example.test",
        "subject_snapshot": "Order confirmed",
        "content_snapshot": "Plain-text alternative",
        "html_snapshot": "<p>Order confirmed</p>",
        "scheduled_at": None,
        "campaign_id": 42,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


class TwilioEmailProviderTests(SimpleTestCase):
    @override_settings(**EMAIL_SETTINGS)
    @patch("functionalities.marketing.providers.twilio_email.requests.post")
    def test_send_email_uses_comms_endpoint_api_key_auth_and_snapshot(self, post):
        post.return_value = Mock(status_code=202, json=lambda: {"id": "email-operation-1"})

        result = send_email(message())

        self.assertEqual(result.provider_id, "email-operation-1")
        self.assertEqual(result.status, "accepted")
        post.assert_called_once()
        args, kwargs = post.call_args
        self.assertEqual(args[0], "https://comms.twilio.com/v1/Emails")
        self.assertEqual(kwargs["auth"], ("SK_email", "email-secret"))
        self.assertEqual(kwargs["timeout"], (5, 30))
        self.assertEqual(kwargs["json"]["from"]["address"], "verified@example.test")
        self.assertEqual(kwargs["json"]["to"], [{"address": "recipient@example.test"}])
        self.assertEqual(kwargs["json"]["content"]["text"], "Plain-text alternative")
        self.assertIn("html", kwargs["json"]["content"])
        self.assertEqual(kwargs["json"]["tags"][0]["value"], "42")

    @override_settings(**EMAIL_SETTINGS)
    @patch("functionalities.marketing.providers.twilio_email.requests.post")
    def test_email_classifies_validation_rate_server_timeout_and_bad_json(self, post):
        scenarios = (
            (Mock(status_code=400, json=lambda: {"message": "email-secret invalid"}), False, 400),
            (Mock(status_code=429, json=lambda: {"message": "limited"}), True, 429),
            (Mock(status_code=503, json=lambda: {"message": "down"}), True, 503),
        )
        for response, retryable, status_code in scenarios:
            with self.subTest(status_code=status_code):
                post.return_value = response
                with self.assertRaises(ProviderError) as caught:
                    send_email(message())
                self.assertEqual(caught.exception.retryable, retryable)
                self.assertEqual(caught.exception.status_code, status_code)
                self.assertNotIn("email-secret", str(caught.exception))

        post.side_effect = requests.Timeout("email-secret timed out")
        with self.assertRaises(ProviderError) as caught:
            send_email(message())
        self.assertTrue(caught.exception.retryable)
        self.assertNotIn("email-secret", str(caught.exception))

        post.side_effect = None
        post.return_value = Mock(status_code=202, json=Mock(side_effect=ValueError("bad json")))
        with self.assertRaises(ProviderError) as caught:
            send_email(message())
        self.assertTrue(caught.exception.retryable)

    @override_settings(**EMAIL_SETTINGS)
    @patch("functionalities.marketing.providers.twilio_email.requests.get")
    def test_fetch_email_operation_uses_bounded_timeout(self, get):
        get.return_value = Mock(status_code=200, json=lambda: {"id": "op-1", "status": "delivered"})

        result = fetch_email_operation("op-1")

        self.assertEqual(result.status, "delivered")
        get.assert_called_once_with(
            "https://comms.twilio.com/v1/Emails/op-1",
            auth=("SK_email", "email-secret"),
            timeout=(5, 30),
        )


class TwilioSmsProviderTests(SimpleTestCase):
    @override_settings(**SMS_SETTINGS)
    @patch("functionalities.marketing.providers.twilio_sms.Client")
    def test_sms_uses_api_key_client_sender_and_status_callback(self, client_class):
        client_class.return_value.messages.create.return_value = SimpleNamespace(sid="SM123", status="queued")

        result = send_sms(message(destination="+27728864770", content_snapshot="Appointment reminder"))

        client_class.assert_called_once_with("SK_sms", "sms-secret", account_sid="AC_account")
        client_class.return_value.messages.create.assert_called_once_with(
            to="+27728864770",
            from_="+17372508034",
            body="Appointment reminder",
            status_callback="https://example.test/growth/webhooks/twilio/sms/",
        )
        self.assertEqual((result.provider_id, result.status), ("SM123", "accepted"))

    @override_settings(**{**SMS_SETTINGS, "TWILIO_SMS_FROM_NUMBER": "", "TWILIO_MESSAGING_SERVICE_SID": "MG123"})
    @patch("functionalities.marketing.providers.twilio_sms.Client")
    def test_sms_supports_messaging_service(self, client_class):
        client_class.return_value.messages.create.return_value = SimpleNamespace(sid="SM456", status="sent")
        send_sms(message(destination="+27728864770", content_snapshot="Reminder"))
        self.assertEqual(client_class.return_value.messages.create.call_args.kwargs["messaging_service_sid"], "MG123")
        self.assertNotIn("from_", client_class.return_value.messages.create.call_args.kwargs)

    @override_settings(**{**SMS_SETTINGS, "TWILIO_SMS_FROM_NUMBER": "", "TWILIO_MESSAGING_SERVICE_SID": ""})
    @patch("functionalities.marketing.providers.twilio_sms.Client")
    def test_sms_rejects_invalid_destination_or_missing_sender_before_sdk_call(self, client_class):
        for destination in ("0728864770", "not-a-number"):
            with self.subTest(destination=destination), self.assertRaises(ProviderError):
                send_sms(message(destination=destination))
        with self.assertRaises(ProviderError):
            send_sms(message(destination="+27728864770"))
        client_class.assert_not_called()

    @override_settings(**SMS_SETTINGS)
    @patch("functionalities.marketing.providers.twilio_sms.Client")
    def test_sms_provider_errors_are_classified_and_redacted(self, client_class):
        error = Exception("sms-secret is invalid")
        error.status = 429
        error.code = 20429
        client_class.return_value.messages.create.side_effect = error

        with self.assertRaises(ProviderError) as caught:
            send_sms(message(destination="+27728864770"))

        self.assertTrue(caught.exception.retryable)
        self.assertEqual(caught.exception.status_code, 429)
        self.assertNotIn("sms-secret", str(caught.exception))

    @override_settings(TWILIO_AUTH_TOKEN="auth-token")
    @patch("functionalities.marketing.providers.twilio_sms.RequestValidator")
    def test_signature_validation_uses_official_twilio_validator(self, validator_class):
        validator_class.return_value.validate.return_value = True

        valid = validate_twilio_request(
            url="https://example.test/webhook",
            params={"MessageSid": "SM123"},
            signature="signed-value",
        )

        self.assertTrue(valid)
        validator_class.assert_called_once_with("auth-token")
        validator_class.return_value.validate.assert_called_once_with(
            "https://example.test/webhook", {"MessageSid": "SM123"}, "signed-value"
        )
