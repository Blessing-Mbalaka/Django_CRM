from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase, TransactionTestCase
from django.utils import timezone

from apps.marketing.models import DeliveryAttempt, MarketingContact, OutboundMessage
from functionalities.marketing.dispatch import cancel_message, dispatch_message, queue_message, retry_message
from functionalities.marketing.providers.base import ProviderError, ProviderResult
from functionalities.marketing.scheduling import dispatch_due_marketing


class DispatchTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.manager = User.objects.create_user(username="manager", role=User.Role.ADMIN)
        self.reader = User.objects.create_user(username="reader", role=User.Role.STAFF)
        self.contact = MarketingContact.objects.create(
            name="Recipient",
            email="person@example.test",
            mobile_number="+27728864770",
            whatsapp_number="+27728864770",
            email_consent=True,
            sms_consent=True,
            whatsapp_consent=True,
        )

    def test_queue_requires_manager_and_persists_contact_snapshot(self):
        with self.assertRaises(PermissionDenied):
            queue_message(channel="email", actor=self.reader, contact=self.contact, body="Hello")

        queued = queue_message(
            channel="email", actor=self.manager, contact=self.contact,
            subject="Welcome", body="Hello", html="<p>Hello</p>",
        )
        self.assertEqual(queued.destination, "person@example.test")
        self.assertEqual(queued.content_snapshot, "Hello")
        self.assertEqual(queued.status, OutboundMessage.Status.DRAFT)

    @patch("functionalities.marketing.dispatch.PROVIDERS")
    def test_each_channel_selects_its_adapter_and_acceptance_is_not_delivery(self, providers):
        for channel in OutboundMessage.Channel.values:
            with self.subTest(channel=channel):
                adapter = Mock(return_value=ProviderResult(f"id-{channel}", "accepted", {}, False))
                providers.__getitem__.return_value = (f"provider-{channel}", adapter)
                contact = self.contact if channel in {"email", "sms", "whatsapp"} else None
                destination = "configured-page" if contact is None else ""
                queued = queue_message(
                    channel=channel, actor=self.manager, contact=contact, destination=destination,
                    subject="Subject", body="Body", media_url="https://cdn.example.test/a.jpg",
                )
                sent = dispatch_message(queued.pk)
                self.assertEqual(sent.status, OutboundMessage.Status.ACCEPTED)
                self.assertIsNone(sent.delivered_at)
                adapter.assert_called_once()

    @patch("functionalities.marketing.dispatch.PROVIDERS")
    def test_opt_out_and_bad_destination_stop_before_provider_call(self, providers):
        adapter = Mock()
        providers.__getitem__.return_value = ("twilio_sms", adapter)
        self.contact.sms_opted_out_at = timezone.now()
        self.contact.save()
        with self.assertRaises(ValidationError):
            queue_message(channel="sms", actor=self.manager, contact=self.contact, body="No")

        self.contact.sms_opted_out_at = None
        self.contact.mobile_number = "0728864770"
        self.contact.save()
        queued = OutboundMessage.objects.create(
            channel="sms", contact=self.contact, destination="0728864770", content_snapshot="Bad", created_by=self.manager
        )
        dispatch_message(queued.pk)
        queued.refresh_from_db()
        self.assertEqual(queued.status, OutboundMessage.Status.FAILED)
        adapter.assert_not_called()

    @patch("functionalities.marketing.dispatch.PROVIDERS")
    def test_attempts_and_retry_classification_are_persisted_without_secret_text(self, providers):
        providers.__getitem__.return_value = (
            "twilio_sms",
            Mock(side_effect=ProviderError("super-secret provider text", retryable=True, status_code=503)),
        )
        queued = queue_message(channel="sms", actor=self.manager, contact=self.contact, body="Hello")
        dispatch_message(queued.pk)
        queued.refresh_from_db()
        attempt = DeliveryAttempt.objects.get(message=queued)
        self.assertEqual(queued.status, OutboundMessage.Status.FAILED)
        self.assertEqual(queued.last_error, "Delivery provider temporarily failed.")
        self.assertTrue(attempt.retryable)
        self.assertNotIn("super-secret", attempt.error)

        retry_message(message=queued, actor=self.manager)
        queued.refresh_from_db()
        self.assertEqual(queued.status, OutboundMessage.Status.DRAFT)

    def test_retry_limit_cancellation_and_actor_requirements(self):
        message = OutboundMessage.objects.create(
            channel="email", destination="person@example.test", content_snapshot="Body",
            status=OutboundMessage.Status.FAILED, attempt_count=3, created_by=self.manager,
        )
        with self.assertRaises(ValidationError):
            retry_message(message=message, actor=self.manager)
        with self.assertRaises(PermissionDenied):
            cancel_message(message=message, actor=self.reader)
        message.attempt_count = 1
        message.save(update_fields=["attempt_count", "updated_at"])
        cancelled = cancel_message(message=message, actor=self.manager)
        self.assertEqual(cancelled.status, OutboundMessage.Status.CANCELLED)


class SchedulerTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        User = get_user_model()
        self.manager = User.objects.create_user(username="scheduler-manager", role=User.Role.ADMIN)

    @patch("functionalities.marketing.dispatch.PROVIDERS")
    def test_due_messages_are_ordered_limited_and_not_sent_twice(self, providers):
        adapter = Mock(return_value=ProviderResult("provider-id", "accepted", {}, False))
        providers.__getitem__.return_value = ("twilio_email", adapter)
        now = timezone.now()
        first = OutboundMessage.objects.create(
            channel="email", destination="one@example.test", content_snapshot="One",
            status="scheduled", scheduled_at=now - timedelta(minutes=2), created_by=self.manager,
        )
        second = OutboundMessage.objects.create(
            channel="email", destination="two@example.test", content_snapshot="Two",
            status="scheduled", scheduled_at=now - timedelta(minutes=1), created_by=self.manager,
        )
        OutboundMessage.objects.create(
            channel="email", destination="future@example.test", content_snapshot="Future",
            status="scheduled", scheduled_at=now + timedelta(hours=1), created_by=self.manager,
        )
        summary = dispatch_due_marketing(limit=1)
        duplicate = dispatch_message(first.pk)
        self.assertEqual(summary.dispatched, 1)
        self.assertEqual(adapter.call_count, 1)
        self.assertEqual(duplicate.status, OutboundMessage.Status.ACCEPTED)
        second.refresh_from_db()
        self.assertEqual(second.status, OutboundMessage.Status.SCHEDULED)

    @patch("functionalities.marketing.dispatch.PROVIDERS")
    def test_stale_processing_claim_is_recovered_and_adapter_crash_is_isolated(self, providers):
        providers.__getitem__.return_value = ("twilio_email", Mock(side_effect=RuntimeError("boom")))
        stale = OutboundMessage.objects.create(
            channel="email", destination="stale@example.test", content_snapshot="Stale",
            status="processing", scheduled_at=timezone.now() - timedelta(hours=1), created_by=self.manager,
        )
        OutboundMessage.objects.filter(pk=stale.pk).update(updated_at=timezone.now() - timedelta(hours=1))
        summary = dispatch_due_marketing(limit=10)
        stale.refresh_from_db()
        self.assertEqual(summary.failed, 1)
        self.assertEqual(stale.status, OutboundMessage.Status.FAILED)

