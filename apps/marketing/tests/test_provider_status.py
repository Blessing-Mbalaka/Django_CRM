from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from functionalities.marketing.providers.base import ProviderError, ProviderResult
from functionalities.marketing.providers.status import ProviderState, provider_status


EMPTY_PROVIDER_SETTINGS = {
    "TWILIO_EMAIL_API_KEY": "",
    "TWILIO_EMAIL_API_SECRET": "",
    "TWILIO_EMAIL_FROM_ADDRESS": "",
    "TWILIO_EMAIL_FROM_NAME": "",
    "TWILIO_ACCOUNT_SID": "",
    "TWILIO_API_KEY": "",
    "TWILIO_API_SECRET": "",
    "TWILIO_AUTH_TOKEN": "",
    "TWILIO_SMS_FROM_NUMBER": "",
    "TWILIO_MESSAGING_SERVICE_SID": "",
    "TWILIO_STATUS_CALLBACK_URL": "",
    "META_GRAPH_API_VERSION": "",
    "META_ACCESS_TOKEN": "",
    "META_APP_SECRET": "",
    "META_WEBHOOK_VERIFY_TOKEN": "",
    "META_WHATSAPP_PHONE_NUMBER_ID": "",
    "META_WHATSAPP_BUSINESS_ACCOUNT_ID": "",
    "META_FACEBOOK_PAGE_ID": "",
    "META_FACEBOOK_PAGE_ACCESS_TOKEN": "",
    "META_INSTAGRAM_USER_ID": "",
    "META_INSTAGRAM_ACCESS_TOKEN": "",
    "MARKETING_PUBLIC_BASE_URL": "",
}


class ProviderPrimitiveTests(SimpleTestCase):
    def test_result_is_immutable_and_error_exposes_only_safe_details(self):
        result = ProviderResult("SM123", "accepted", {"segment_count": 1}, retryable=False)
        with self.assertRaises(Exception):
            result.status = "delivered"

        error = ProviderError("Provider rejected the request", retryable=False, status_code=400, safe_details={"code": 123})
        self.assertEqual(error.safe_details, {"code": 123})
        self.assertNotIn("authorization", str(error).lower())


class ProviderStatusTests(SimpleTestCase):
    @override_settings(**EMPTY_PROVIDER_SETTINGS)
    def test_empty_configuration_reports_each_provider_independently(self):
        statuses = provider_status()

        self.assertEqual(
            set(statuses),
            {"twilio_email", "twilio_sms", "meta_whatsapp", "meta_facebook", "meta_instagram"},
        )
        self.assertTrue(all(item.state is ProviderState.NOT_CONFIGURED for item in statuses.values()))
        self.assertIn("TWILIO_EMAIL_API_KEY", statuses["twilio_email"].missing)
        self.assertNotIn("TWILIO_EMAIL_API_KEY", statuses["meta_whatsapp"].missing)

    @override_settings(**{
        **EMPTY_PROVIDER_SETTINGS,
        "TWILIO_EMAIL_API_KEY": "SK_email",
        "TWILIO_EMAIL_API_SECRET": "email-secret",
        "TWILIO_EMAIL_FROM_ADDRESS": "verified@example.test",
        "TWILIO_EMAIL_FROM_NAME": "Example Business",
    })
    def test_complete_email_configuration_is_available_without_a_probe(self):
        with patch("functionalities.marketing.providers.status.requests.get") as request:
            status = provider_status()["twilio_email"]

        self.assertIs(status.state, ProviderState.AVAILABLE)
        request.assert_not_called()

    def test_each_missing_email_value_is_named_without_leaking_other_values(self):
        complete = {
            **EMPTY_PROVIDER_SETTINGS,
            "TWILIO_EMAIL_API_KEY": "SK_email_private",
            "TWILIO_EMAIL_API_SECRET": "email-secret-private",
            "TWILIO_EMAIL_FROM_ADDRESS": "verified@example.test",
            "TWILIO_EMAIL_FROM_NAME": "Example Business",
        }
        for missing_name in (
            "TWILIO_EMAIL_API_KEY",
            "TWILIO_EMAIL_API_SECRET",
            "TWILIO_EMAIL_FROM_ADDRESS",
            "TWILIO_EMAIL_FROM_NAME",
        ):
            configured = {**complete, missing_name: ""}
            with self.subTest(missing_name=missing_name), override_settings(**configured):
                status = provider_status()["twilio_email"]
                rendered = f"{status.message} {status.missing}"
                self.assertIs(status.state, ProviderState.NOT_CONFIGURED)
                self.assertIn(missing_name, status.missing)
                self.assertNotIn("private", rendered)

    def test_sms_accepts_either_sender_number_or_messaging_service(self):
        base = {
            **EMPTY_PROVIDER_SETTINGS,
            "TWILIO_ACCOUNT_SID": "AC_private",
            "TWILIO_API_KEY": "SK_private",
            "TWILIO_API_SECRET": "secret-private",
            "TWILIO_AUTH_TOKEN": "auth-private",
            "TWILIO_STATUS_CALLBACK_URL": "https://example.test/growth/webhooks/twilio/sms/",
        }
        for sender_setting in ("TWILIO_SMS_FROM_NUMBER", "TWILIO_MESSAGING_SERVICE_SID"):
            with self.subTest(sender_setting=sender_setting), override_settings(**{**base, sender_setting: "+15551234567"}):
                self.assertIs(provider_status()["twilio_sms"].state, ProviderState.AVAILABLE)

        with override_settings(**base):
            status = provider_status()["twilio_sms"]
            self.assertIs(status.state, ProviderState.NOT_CONFIGURED)
            self.assertIn("TWILIO_SMS_FROM_NUMBER|TWILIO_MESSAGING_SERVICE_SID", status.missing)

    @override_settings(**{
        **EMPTY_PROVIDER_SETTINGS,
        "META_GRAPH_API_VERSION": "v24.0",
        "META_APP_SECRET": "meta-secret",
        "META_WEBHOOK_VERIFY_TOKEN": "verify-secret",
        "META_ACCESS_TOKEN": "whatsapp-token",
        "META_WHATSAPP_PHONE_NUMBER_ID": "123",
        "META_WHATSAPP_BUSINESS_ACCOUNT_ID": "456",
        "META_FACEBOOK_PAGE_ID": "789",
        "META_FACEBOOK_PAGE_ACCESS_TOKEN": "page-token",
        "META_INSTAGRAM_USER_ID": "321",
        "META_INSTAGRAM_ACCESS_TOKEN": "instagram-token",
        "MARKETING_PUBLIC_BASE_URL": "https://example.test",
    })
    def test_complete_meta_capabilities_are_independently_available(self):
        statuses = provider_status()
        self.assertIs(statuses["meta_whatsapp"].state, ProviderState.AVAILABLE)
        self.assertIs(statuses["meta_facebook"].state, ProviderState.AVAILABLE)
        self.assertIs(statuses["meta_instagram"].state, ProviderState.AVAILABLE)

    @override_settings(**{
        **EMPTY_PROVIDER_SETTINGS,
        "META_GRAPH_API_VERSION": "v24.0",
        "META_APP_SECRET": "meta-secret-private",
        "META_FACEBOOK_PAGE_ID": "789",
        "META_FACEBOOK_PAGE_ACCESS_TOKEN": "page-token-private",
    })
    @patch("functionalities.marketing.providers.status.requests.get", side_effect=TimeoutError("page-token-private timed out"))
    def test_failing_optional_probe_is_safely_reported(self, request):
        status = provider_status(probe=True)["meta_facebook"]

        self.assertIs(status.state, ProviderState.TEMPORARILY_FAILING)
        self.assertEqual(status.missing, ())
        self.assertNotIn("private", status.message)
        request.assert_called_once()
