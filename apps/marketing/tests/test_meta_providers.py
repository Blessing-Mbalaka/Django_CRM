import hashlib
import hmac
from types import SimpleNamespace
from unittest.mock import Mock, call, patch

import requests
from django.test import SimpleTestCase, override_settings

from functionalities.marketing.providers.base import ProviderError
from functionalities.marketing.providers.meta_common import validate_meta_signature
from functionalities.marketing.providers.meta_facebook import publish_facebook_post
from functionalities.marketing.providers.meta_instagram import create_instagram_container, publish_instagram_media
from functionalities.marketing.providers.meta_whatsapp import send_whatsapp


META_SETTINGS = {
    "META_GRAPH_API_VERSION": "v24.0",
    "META_ACCESS_TOKEN": "wa-token",
    "META_APP_SECRET": "app-secret",
    "META_WHATSAPP_PHONE_NUMBER_ID": "phone-123",
    "META_FACEBOOK_PAGE_ID": "page-123",
    "META_FACEBOOK_PAGE_ACCESS_TOKEN": "page-token",
    "META_INSTAGRAM_USER_ID": "ig-123",
    "META_INSTAGRAM_ACCESS_TOKEN": "ig-token",
    "MARKETING_PUBLIC_BASE_URL": "https://crm.example.test",
}


def message(**overrides):
    values = {
        "destination": "+27728864770",
        "content_snapshot": "New product available",
        "media_url_snapshot": "https://cdn.example.test/poster.jpg",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


class MetaWhatsAppTests(SimpleTestCase):
    @override_settings(**META_SETTINGS)
    @patch("functionalities.marketing.providers.meta_common.requests.post")
    def test_whatsapp_uses_versioned_graph_url_bearer_token_and_returns_wamid(self, post):
        post.return_value = Mock(status_code=200, json=lambda: {"messages": [{"id": "wamid.123"}]})

        result = send_whatsapp(message())

        self.assertEqual((result.provider_id, result.status), ("wamid.123", "accepted"))
        args, kwargs = post.call_args
        self.assertEqual(args[0], "https://graph.facebook.com/v24.0/phone-123/messages")
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer wa-token")
        self.assertEqual(kwargs["timeout"], (5, 30))
        self.assertEqual(kwargs["json"]["to"], "+27728864770")
        self.assertEqual(kwargs["json"]["text"]["body"], "New product available")

    @override_settings(**META_SETTINGS)
    @patch("functionalities.marketing.providers.meta_common.requests.post")
    def test_whatsapp_template_payload_and_content_validation(self, post):
        post.return_value = Mock(status_code=200, json=lambda: {"messages": [{"id": "wamid.456"}]})
        template_message = message(content_snapshot="", template_name="appointment_reminder", template_language="en_US")
        send_whatsapp(template_message)
        payload = post.call_args.kwargs["json"]
        self.assertEqual(payload["type"], "template")
        self.assertEqual(payload["template"]["name"], "appointment_reminder")

        with self.assertRaises(ProviderError):
            send_whatsapp(message(content_snapshot="", template_name=""))

    @override_settings(**META_SETTINGS)
    @patch("functionalities.marketing.providers.meta_common.requests.post")
    def test_meta_errors_classify_rate_limits_timeouts_and_hide_tokens(self, post):
        post.return_value = Mock(status_code=429, json=lambda: {"error": {"message": "wa-token exhausted", "code": 4}})
        with self.assertRaises(ProviderError) as caught:
            send_whatsapp(message())
        self.assertTrue(caught.exception.retryable)
        self.assertNotIn("wa-token", str(caught.exception))

        post.side_effect = requests.Timeout("wa-token timed out")
        with self.assertRaises(ProviderError) as caught:
            send_whatsapp(message())
        self.assertTrue(caught.exception.retryable)


class MetaPublishingTests(SimpleTestCase):
    @override_settings(**META_SETTINGS)
    @patch("functionalities.marketing.providers.meta_common.requests.post")
    def test_facebook_publishes_only_to_configured_page(self, post):
        post.return_value = Mock(status_code=200, json=lambda: {"id": "page-123_99"})

        result = publish_facebook_post(message())

        self.assertEqual(result.provider_id, "page-123_99")
        args, kwargs = post.call_args
        self.assertEqual(args[0], "https://graph.facebook.com/v24.0/page-123/feed")
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer page-token")
        self.assertEqual(kwargs["json"]["message"], "New product available")

    @override_settings(**META_SETTINGS)
    @patch("functionalities.marketing.providers.meta_common.requests.post")
    def test_instagram_creates_then_publishes_a_container(self, post):
        post.side_effect = [
            Mock(status_code=200, json=lambda: {"id": "container-123"}),
            Mock(status_code=200, json=lambda: {"id": "media-123"}),
        ]

        container = create_instagram_container(message())
        published = publish_instagram_media(container.provider_id)

        self.assertEqual(container.provider_id, "container-123")
        self.assertEqual(published.provider_id, "media-123")
        self.assertEqual(
            [entry.args[0] for entry in post.call_args_list],
            [
                "https://graph.facebook.com/v24.0/ig-123/media",
                "https://graph.facebook.com/v24.0/ig-123/media_publish",
            ],
        )
        self.assertEqual(post.call_args_list[0].kwargs["json"]["image_url"], "https://cdn.example.test/poster.jpg")
        self.assertEqual(post.call_args_list[1].kwargs["json"], {"creation_id": "container-123"})

    @override_settings(**META_SETTINGS)
    @patch("functionalities.marketing.providers.meta_common.requests.post")
    def test_instagram_rejects_non_public_or_non_https_media_before_call(self, post):
        for url in (
            "http://cdn.example.test/poster.jpg",
            "https://localhost:8000/media/poster.jpg",
            "https://127.0.0.1/poster.jpg",
            "",
        ):
            with self.subTest(url=url), self.assertRaises(ProviderError):
                create_instagram_container(message(media_url_snapshot=url))
        post.assert_not_called()


class MetaSignatureTests(SimpleTestCase):
    @override_settings(META_APP_SECRET="app-secret")
    def test_valid_signature_is_accepted_and_invalid_or_missing_is_rejected(self):
        raw_body = b'{"object":"whatsapp_business_account"}'
        digest = hmac.new(b"app-secret", raw_body, hashlib.sha256).hexdigest()

        self.assertTrue(validate_meta_signature(raw_body=raw_body, signature_header=f"sha256={digest}"))
        self.assertFalse(validate_meta_signature(raw_body=raw_body, signature_header="sha256=invalid"))
        self.assertFalse(validate_meta_signature(raw_body=raw_body, signature_header=""))

    @override_settings(META_APP_SECRET="")
    def test_empty_app_secret_never_validates(self):
        self.assertFalse(validate_meta_signature(raw_body=b"{}", signature_header="sha256=anything"))

    @override_settings(META_APP_SECRET="app-secret")
    @patch("functionalities.marketing.providers.meta_common.hmac.compare_digest", return_value=True)
    def test_signature_uses_constant_time_comparison(self, compare_digest):
        validate_meta_signature(raw_body=b"{}", signature_header="sha256=digest")
        compare_digest.assert_called_once()
