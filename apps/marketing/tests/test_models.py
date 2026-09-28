from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.marketing.models import (
    BrandKit,
    MarketingCampaign,
    MarketingContact,
    MarketingContent,
    MarketingMetric,
    OutboundMessage,
    ProviderWebhookEvent,
)


class MarketingModelTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="marketing-owner",
            email="owner@example.test",
            password="not-used-in-tests",
        )

    def campaign(self, **overrides):
        values = {
            "name": "Spring launch",
            "start_date": date.today(),
            "end_date": date.today() + timedelta(days=7),
            "budget": Decimal("1000.00"),
            "owner": self.user,
        }
        values.update(overrides)
        return MarketingCampaign(**values)

    def test_campaign_end_date_cannot_precede_start_date(self):
        campaign = self.campaign(end_date=date.today() - timedelta(days=1))

        with self.assertRaisesMessage(ValidationError, "End date cannot precede start date"):
            campaign.full_clean()

    def test_campaign_and_metric_values_cannot_be_negative(self):
        campaign = self.campaign(budget=Decimal("-0.01"))
        with self.assertRaises(ValidationError):
            campaign.full_clean()

        valid_campaign = self.campaign()
        valid_campaign.full_clean()
        valid_campaign.save()
        metric = MarketingMetric(
            campaign=valid_campaign,
            channel=OutboundMessage.Channel.EMAIL,
            reporting_date=date.today(),
            spend=Decimal("-1.00"),
            reach=-1,
        )
        with self.assertRaises(ValidationError):
            metric.full_clean()

    def test_brand_kit_is_a_singleton(self):
        brand = BrandKit.load()
        self.assertEqual(brand.pk, 1)
        self.assertEqual(BrandKit.load().pk, brand.pk)

        with self.assertRaises(ValidationError):
            BrandKit(pk=2, business_name="Second brand").full_clean()

    def test_uploads_are_limited_to_approved_images_under_five_megabytes(self):
        invalid_type = MarketingContent(
            title="Unsafe upload",
            kind=MarketingContent.Kind.POSTER,
            image=SimpleUploadedFile("payload.svg", b"<svg></svg>", content_type="image/svg+xml"),
        )
        with self.assertRaises(ValidationError):
            invalid_type.full_clean()

        too_large = MarketingContent(
            title="Oversized upload",
            kind=MarketingContent.Kind.POSTER,
            image=SimpleUploadedFile("poster.png", b"0" * (5 * 1024 * 1024 + 1), content_type="image/png"),
        )
        with self.assertRaises(ValidationError):
            too_large.full_clean()

        valid = MarketingContent(
            title="Approved upload",
            kind=MarketingContent.Kind.POSTER,
            image=SimpleUploadedFile("poster.png", b"small", content_type="image/png"),
        )
        valid.full_clean()

    def test_opted_out_contact_is_never_eligible_despite_stale_consent(self):
        contact = MarketingContact(
            name="Consent test",
            email="contact@example.test",
            email_consent=True,
            email_opted_out_at="2026-09-28T10:00:00Z",
        )

        self.assertFalse(contact.can_receive(OutboundMessage.Channel.EMAIL))
        with self.assertRaises(ValidationError):
            contact.clean_for_channel(OutboundMessage.Channel.EMAIL)

    def test_provider_event_identity_is_unique_per_provider(self):
        ProviderWebhookEvent.objects.create(provider="twilio_sms", event_id="SM123", event_type="sent")

        with self.assertRaises(IntegrityError), transaction.atomic():
            ProviderWebhookEvent.objects.create(provider="twilio_sms", event_id="SM123", event_type="delivered")

        ProviderWebhookEvent.objects.create(provider="meta_whatsapp", event_id="SM123", event_type="sent")

    def test_outbound_destination_and_content_snapshots_are_immutable(self):
        message = OutboundMessage.objects.create(
            channel=OutboundMessage.Channel.EMAIL,
            destination="first@example.test",
            subject_snapshot="Original subject",
            content_snapshot="Original content",
            created_by=self.user,
        )
        message.destination = "changed@example.test"
        message.content_snapshot = "Changed content"

        with self.assertRaises(ValidationError):
            message.save()

    def test_outbound_delivery_status_choices_are_explicit(self):
        values = {choice.value for choice in OutboundMessage.Status}
        self.assertEqual(
            values,
            {
                "draft",
                "scheduled",
                "processing",
                "accepted",
                "sent",
                "delivered",
                "read",
                "failed",
                "cancelled",
                "unavailable",
            },
        )
