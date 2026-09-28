from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.clients.models import Client
from apps.marketing.models import BrandKit, MarketingCampaign, MarketingContact, MarketingLead, MarketingMetric, OutboundMessage


class MarketingApiTests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.manager = User.objects.create_user(username="api-manager", role=User.Role.ADMIN)
        self.reader = User.objects.create_user(username="api-reader", role=User.Role.STAFF)

    def campaign_payload(self, **overrides):
        payload = {
            "name": "September campaign",
            "start_date": str(date.today()),
            "end_date": str(date.today() + timedelta(days=5)),
            "budget": "1200.00",
            "channels": ["email", "sms"],
        }
        payload.update(overrides)
        return payload

    def test_all_resources_allow_authenticated_reads_but_only_managers_write(self):
        resources = (
            "campaigns", "adverts", "content", "contacts", "leads",
            "activities", "metrics", "brand-kit", "outbound-messages",
        )
        self.client.force_authenticate(self.reader)
        for resource in resources:
            with self.subTest(resource=resource):
                self.assertEqual(self.client.get(f"/api/v1/marketing/{resource}/").status_code, 200)
        self.assertEqual(
            self.client.post("/api/v1/marketing/campaigns/", self.campaign_payload(), format="json").status_code,
            403,
        )
        self.client.force_authenticate(self.manager)
        response = self.client.post("/api/v1/marketing/campaigns/", self.campaign_payload(), format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(MarketingCampaign.objects.get().owner, self.manager)

    def test_api_rejects_invalid_dates_negative_values_and_bad_uploads(self):
        self.client.force_authenticate(self.manager)
        invalid_date = self.client.post(
            "/api/v1/marketing/campaigns/",
            self.campaign_payload(end_date=str(date.today() - timedelta(days=1))), format="json",
        )
        self.assertEqual(invalid_date.status_code, 400)
        negative = self.client.post(
            "/api/v1/marketing/campaigns/", self.campaign_payload(budget="-1.00"), format="json"
        )
        self.assertEqual(negative.status_code, 400)
        bad_image = SimpleUploadedFile("poster.svg", b"<svg></svg>", content_type="image/svg+xml")
        upload = self.client.post(
            "/api/v1/marketing/content/", {"title": "Bad", "kind": "poster", "image": bad_image}, format="multipart"
        )
        self.assertEqual(upload.status_code, 400)

    def test_contact_opt_out_and_singleton_brand_kit(self):
        self.client.force_authenticate(self.manager)
        response = self.client.post(
            "/api/v1/marketing/contacts/",
            {"name": "Contact", "email": "person@example.test", "email_consent": True,
             "email_opted_out_at": timezone.now().isoformat()}, format="json",
        )
        self.assertEqual(response.status_code, 201)
        contact = MarketingContact.objects.get()
        self.assertFalse(contact.can_receive("email"))

        listing = self.client.get("/api/v1/marketing/brand-kit/")
        self.assertEqual(listing.status_code, 200)
        self.assertEqual(BrandKit.objects.count(), 1)
        update = self.client.patch(
            "/api/v1/marketing/brand-kit/1/", {"business_name": "Orange Business"}, format="json"
        )
        self.assertEqual(update.status_code, 200)
        self.assertEqual(BrandKit.load().business_name, "Orange Business")

    def test_summary_calendar_and_analytics_are_database_derived(self):
        self.client.force_authenticate(self.reader)
        campaign = MarketingCampaign.objects.create(
            name="Measured", start_date=date.today(), end_date=date.today() + timedelta(days=2),
            budget=Decimal("500"), owner=self.manager, status="active",
        )
        MarketingMetric.objects.create(
            campaign=campaign, channel="email", reporting_date=date.today(), spend=Decimal("100"),
            reach=1000, enquiries=10, leads=5, customers=2, attributed_revenue=Decimal("400"),
        )
        summary = self.client.get("/api/v1/marketing/workspace/summary/").json()
        calendar = self.client.get("/api/v1/marketing/workspace/calendar/").json()
        analytics = self.client.get("/api/v1/marketing/workspace/analytics/").json()
        self.assertEqual(summary["campaigns"]["active"], 1)
        self.assertTrue(any(item["source"] == "campaign" for item in calendar["results"]))
        self.assertEqual(analytics["totals"]["reach"], 1000)
        self.assertEqual(analytics["roas"], 4.0)

    @override_settings(
        TWILIO_EMAIL_API_KEY="SK", TWILIO_EMAIL_API_SECRET="secret",
        TWILIO_EMAIL_FROM_ADDRESS="sender@example.test", TWILIO_EMAIL_FROM_NAME="Business",
    )
    @patch("apps.marketing.api_views.dispatch_message")
    def test_preview_send_schedule_retry_and_cancel_actions(self, dispatch):
        self.client.force_authenticate(self.manager)
        contact = MarketingContact.objects.create(
            name="Recipient", email="recipient@example.test", email_consent=True,
        )
        preview = self.client.post(
            "/api/v1/marketing/workspace/preview/", {"subject": "Hi", "body": "Welcome"}, format="json"
        )
        self.assertEqual(preview.status_code, 200)
        self.assertIn("Welcome", preview.json()["text"])
        sent = self.client.post(
            "/api/v1/marketing/workspace/send/",
            {"channel": "email", "contact": contact.pk, "subject": "Hi", "body": "Welcome"}, format="json",
        )
        self.assertEqual(sent.status_code, 202)
        dispatch.assert_called_once()
        scheduled = self.client.post(
            "/api/v1/marketing/workspace/schedule/",
            {"channel": "email", "contact": contact.pk, "body": "Later",
             "scheduled_at": (timezone.now() + timedelta(hours=1)).isoformat()}, format="json",
        )
        self.assertEqual(scheduled.status_code, 201)
        message_id = scheduled.json()["id"]
        cancelled = self.client.post(f"/api/v1/marketing/outbound-messages/{message_id}/cancel/")
        self.assertEqual(cancelled.status_code, 200)

    def test_provider_status_has_no_secrets_and_unconfigured_send_is_clear(self):
        self.client.force_authenticate(self.manager)
        response = self.client.get("/api/v1/marketing/workspace/provider-status/")
        rendered = str(response.json())
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("SECRET_KEY", rendered)
        unavailable = self.client.post(
            "/api/v1/marketing/workspace/send/",
            {"channel": "email", "destination": "person@example.test", "body": "Hello"}, format="json",
        )
        self.assertEqual(unavailable.status_code, 503)
        self.assertIn("not configured", str(unavailable.json()).lower())

    def test_lead_conversion_reuses_existing_client(self):
        self.client.force_authenticate(self.manager)
        contact = MarketingContact.objects.create(name="Acme", email="hello@acme.test")
        existing = Client.objects.create(name="Acme")
        lead = MarketingLead.objects.create(contact=contact, owner=self.manager)
        first = self.client.post(f"/api/v1/marketing/leads/{lead.pk}/convert-to-client/")
        second = self.client.post(f"/api/v1/marketing/leads/{lead.pk}/convert-to-client/")
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(Client.objects.filter(name="Acme").count(), 1)
        lead.refresh_from_db()
        self.assertEqual(lead.client, existing)
