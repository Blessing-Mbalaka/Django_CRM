from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.deconstruct import deconstructible


MAX_IMAGE_BYTES = 5 * 1024 * 1024
APPROVED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
APPROVED_IMAGE_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}


@deconstructible
class MarketingImageValidator:
    def __call__(self, uploaded_file):
        extension = Path(uploaded_file.name).suffix.lower()
        content_type = getattr(uploaded_file, "content_type", "")
        errors = []
        if extension not in APPROVED_IMAGE_EXTENSIONS or (
            content_type and content_type not in APPROVED_IMAGE_MIME_TYPES
        ):
            errors.append("Upload a JPG, PNG, or WebP image.")
        if uploaded_file.size > MAX_IMAGE_BYTES:
            errors.append("Image uploads cannot exceed 5 MB.")
        if errors:
            raise ValidationError(errors)


validate_marketing_image = MarketingImageValidator()


def content_upload_path(instance, filename):
    extension = Path(filename).suffix.lower()
    now = timezone.now()
    return f"marketing/content/{now:%Y/%m}/{uuid4().hex}{extension}"


def brand_upload_path(instance, filename):
    extension = Path(filename).suffix.lower()
    return f"marketing/brand/{uuid4().hex}{extension}"


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class MarketingCampaign(TimestampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SCHEDULED = "scheduled", "Scheduled"
        ACTIVE = "active", "Active"
        PAUSED = "paused", "Paused"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    name = models.CharField(max_length=200)
    objective = models.CharField(max_length=255, blank=True)
    product_service = models.CharField(max_length=255, blank=True)
    target_audience = models.TextField(blank=True)
    target_location = models.CharField(max_length=255, blank=True)
    channels = models.JSONField(default=list, blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    budget = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="marketing_campaigns",
    )

    class Meta:
        ordering = ["-start_date", "name"]
        constraints = [
            models.CheckConstraint(condition=models.Q(budget__gte=0), name="marketing_campaign_budget_gte_0"),
        ]

    def clean(self):
        super().clean()
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError({"end_date": "End date cannot precede start date."})

    def __str__(self):
        return self.name


class MarketingAdvert(TimestampedModel):
    campaign = models.ForeignKey(MarketingCampaign, on_delete=models.CASCADE, related_name="adverts")
    name = models.CharField(max_length=200)
    advertised_subject = models.CharField(max_length=255, blank=True)
    advertising_type = models.CharField(max_length=80, blank=True)
    platform = models.CharField(max_length=80, blank=True)
    audience = models.TextField(blank=True)
    location = models.CharField(max_length=255, blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    budget = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    actual_spend = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    destination_url = models.URLField(blank=True)
    status = models.CharField(max_length=20, choices=MarketingCampaign.Status.choices, default=MarketingCampaign.Status.DRAFT)

    class Meta:
        ordering = ["-start_date", "name"]
        constraints = [
            models.CheckConstraint(condition=models.Q(budget__gte=0), name="marketing_advert_budget_gte_0"),
            models.CheckConstraint(condition=models.Q(actual_spend__gte=0), name="marketing_advert_spend_gte_0"),
        ]

    def clean(self):
        super().clean()
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError({"end_date": "End date cannot precede start date."})

    def __str__(self):
        return self.name


class MarketingContent(TimestampedModel):
    class Kind(models.TextChoices):
        POSTER = "poster", "Poster"
        SOCIAL = "social", "Social"
        EMAIL = "email", "Email"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SCHEDULED = "scheduled", "Scheduled"
        PUBLISHED = "published", "Published"
        ARCHIVED = "archived", "Archived"

    campaign = models.ForeignKey(MarketingCampaign, null=True, blank=True, on_delete=models.SET_NULL, related_name="content")
    kind = models.CharField(max_length=20, choices=Kind.choices)
    title = models.CharField(max_length=200)
    subject = models.CharField(max_length=255, blank=True)
    heading = models.CharField(max_length=255, blank=True)
    body = models.TextField(blank=True)
    call_to_action = models.CharField(max_length=120, blank=True)
    call_to_action_url = models.URLField(blank=True)
    hashtags = models.CharField(max_length=500, blank=True)
    platform = models.CharField(max_length=80, blank=True)
    template = models.CharField(max_length=80, blank=True)
    image = models.ImageField(upload_to=content_upload_path, validators=[validate_marketing_image], blank=True)
    scheduled_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class MarketingContact(TimestampedModel):
    name = models.CharField(max_length=200)
    email = models.EmailField(blank=True)
    mobile_number = models.CharField(max_length=32, blank=True)
    whatsapp_number = models.CharField(max_length=32, blank=True)
    source = models.CharField(max_length=120, blank=True)
    client = models.ForeignKey("clients.Client", null=True, blank=True, on_delete=models.SET_NULL, related_name="marketing_contacts")
    email_consent = models.BooleanField(default=False)
    sms_consent = models.BooleanField(default=False)
    whatsapp_consent = models.BooleanField(default=False)
    email_consented_at = models.DateTimeField(null=True, blank=True)
    sms_consented_at = models.DateTimeField(null=True, blank=True)
    whatsapp_consented_at = models.DateTimeField(null=True, blank=True)
    consent_source = models.CharField(max_length=120, blank=True)
    email_opted_out_at = models.DateTimeField(null=True, blank=True)
    sms_opted_out_at = models.DateTimeField(null=True, blank=True)
    whatsapp_opted_out_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def destination_for(self, channel):
        return {
            OutboundMessage.Channel.EMAIL: self.email,
            OutboundMessage.Channel.SMS: self.mobile_number,
            OutboundMessage.Channel.WHATSAPP: self.whatsapp_number,
        }.get(channel, "")

    def can_receive(self, channel):
        fields = {
            OutboundMessage.Channel.EMAIL: (self.email_consent, self.email_opted_out_at),
            OutboundMessage.Channel.SMS: (self.sms_consent, self.sms_opted_out_at),
            OutboundMessage.Channel.WHATSAPP: (self.whatsapp_consent, self.whatsapp_opted_out_at),
        }
        if channel not in fields:
            return False
        consented, opted_out_at = fields[channel]
        return bool(self.is_active and consented and not opted_out_at and self.destination_for(channel))

    def clean_for_channel(self, channel):
        if not self.can_receive(channel):
            raise ValidationError("Contact does not have active consent and a usable destination for this channel.")

    def __str__(self):
        return self.name


class MarketingLead(TimestampedModel):
    class Status(models.TextChoices):
        NEW = "new", "New"
        CONTACTED = "contacted", "Contacted"
        INTERESTED = "interested", "Interested"
        CONVERTED = "converted", "Converted"
        NOT_INTERESTED = "not_interested", "Not interested"

    contact = models.ForeignKey(MarketingContact, null=True, blank=True, on_delete=models.SET_NULL, related_name="leads")
    campaign = models.ForeignKey(MarketingCampaign, null=True, blank=True, on_delete=models.SET_NULL, related_name="leads")
    acquisition_source = models.CharField(max_length=120, blank=True)
    received_date = models.DateField(default=timezone.localdate)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
    estimated_value = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="marketing_leads")
    client = models.ForeignKey("clients.Client", null=True, blank=True, on_delete=models.SET_NULL, related_name="marketing_leads")

    class Meta:
        ordering = ["-received_date", "-created_at"]
        constraints = [models.CheckConstraint(condition=models.Q(estimated_value__gte=0), name="marketing_lead_value_gte_0")]


class MarketingActivity(TimestampedModel):
    name = models.CharField(max_length=200)
    activity_type = models.CharField(max_length=80)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField(null=True, blank=True)
    description = models.TextField(blank=True)
    campaign = models.ForeignKey(MarketingCampaign, null=True, blank=True, on_delete=models.CASCADE, related_name="activities")
    advert = models.ForeignKey(MarketingAdvert, null=True, blank=True, on_delete=models.CASCADE, related_name="activities")
    content = models.ForeignKey(MarketingContent, null=True, blank=True, on_delete=models.CASCADE, related_name="activities")

    class Meta:
        ordering = ["starts_at"]

    def clean(self):
        super().clean()
        if self.ends_at and self.starts_at and self.ends_at < self.starts_at:
            raise ValidationError({"ends_at": "End time cannot precede start time."})


class MarketingMetric(TimestampedModel):
    campaign = models.ForeignKey(MarketingCampaign, on_delete=models.CASCADE, related_name="metrics")
    advert = models.ForeignKey(MarketingAdvert, null=True, blank=True, on_delete=models.SET_NULL, related_name="metrics")
    channel = models.CharField(max_length=20)
    reporting_date = models.DateField()
    period = models.CharField(max_length=40, blank=True)
    spend = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    reach = models.PositiveBigIntegerField(default=0)
    responses = models.PositiveBigIntegerField(default=0)
    enquiries = models.PositiveBigIntegerField(default=0)
    leads = models.PositiveBigIntegerField(default=0)
    customers = models.PositiveBigIntegerField(default=0)
    attributed_revenue = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    class Meta:
        ordering = ["-reporting_date"]
        constraints = [
            models.CheckConstraint(condition=models.Q(spend__gte=0), name="marketing_metric_spend_gte_0"),
            models.CheckConstraint(condition=models.Q(reach__gte=0), name="marketing_metric_reach_gte_0"),
            models.CheckConstraint(condition=models.Q(responses__gte=0), name="marketing_metric_responses_gte_0"),
            models.CheckConstraint(condition=models.Q(enquiries__gte=0), name="marketing_metric_enquiries_gte_0"),
            models.CheckConstraint(condition=models.Q(leads__gte=0), name="marketing_metric_leads_gte_0"),
            models.CheckConstraint(condition=models.Q(customers__gte=0), name="marketing_metric_customers_gte_0"),
            models.CheckConstraint(condition=models.Q(attributed_revenue__gte=0), name="marketing_metric_revenue_gte_0"),
        ]


class BrandKit(TimestampedModel):
    business_name = models.CharField(max_length=200, blank=True)
    slogan = models.CharField(max_length=255, blank=True)
    logo = models.ImageField(upload_to=brand_upload_path, validators=[validate_marketing_image], blank=True)
    primary_colour = models.CharField(max_length=20, blank=True)
    secondary_colour = models.CharField(max_length=20, blank=True)
    accent_colour = models.CharField(max_length=20, blank=True)
    heading_font = models.CharField(max_length=100, blank=True)
    body_font = models.CharField(max_length=100, blank=True)
    short_description = models.TextField(blank=True)
    long_description = models.TextField(blank=True)
    phone = models.CharField(max_length=32, blank=True)
    whatsapp = models.CharField(max_length=32, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    physical_location = models.TextField(blank=True)
    facebook_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def clean(self):
        super().clean()
        if self.pk not in (None, 1):
            raise ValidationError("Only one Brand Kit can exist.")

    def save(self, *args, **kwargs):
        self.pk = 1
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.business_name or "Brand Kit"


class OutboundMessage(TimestampedModel):
    class Channel(models.TextChoices):
        EMAIL = "email", "Email"
        SMS = "sms", "SMS"
        WHATSAPP = "whatsapp", "WhatsApp"
        FACEBOOK = "facebook", "Facebook"
        INSTAGRAM = "instagram", "Instagram"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SCHEDULED = "scheduled", "Scheduled"
        PROCESSING = "processing", "Processing"
        ACCEPTED = "accepted", "Accepted"
        SENT = "sent", "Sent"
        DELIVERED = "delivered", "Delivered"
        READ = "read", "Read"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"
        UNAVAILABLE = "unavailable", "Unavailable"

    channel = models.CharField(max_length=20, choices=Channel.choices)
    campaign = models.ForeignKey(MarketingCampaign, null=True, blank=True, on_delete=models.SET_NULL, related_name="outbound_messages")
    content = models.ForeignKey(MarketingContent, null=True, blank=True, on_delete=models.SET_NULL, related_name="outbound_messages")
    contact = models.ForeignKey(MarketingContact, null=True, blank=True, on_delete=models.SET_NULL, related_name="outbound_messages")
    destination = models.CharField(max_length=320, blank=True)
    subject_snapshot = models.CharField(max_length=255, blank=True)
    content_snapshot = models.TextField()
    html_snapshot = models.TextField(blank=True)
    media_url_snapshot = models.URLField(blank=True)
    scheduled_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    provider = models.CharField(max_length=40, blank=True)
    provider_message_id = models.CharField(max_length=255, blank=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)
    attempt_count = models.PositiveIntegerField(default=0)
    last_error = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="created_marketing_messages")

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if self.pk:
            persisted = type(self).objects.only(
                "destination", "subject_snapshot", "content_snapshot", "html_snapshot", "media_url_snapshot"
            ).get(pk=self.pk)
            immutable_fields = (
                "destination",
                "subject_snapshot",
                "content_snapshot",
                "html_snapshot",
                "media_url_snapshot",
            )
            if any(getattr(self, field) != getattr(persisted, field) for field in immutable_fields):
                raise ValidationError("Outbound destination and content snapshots are immutable after creation.")
        return super().save(*args, **kwargs)


class DeliveryAttempt(models.Model):
    message = models.ForeignKey(OutboundMessage, on_delete=models.CASCADE, related_name="delivery_attempts")
    attempt_number = models.PositiveIntegerField()
    started_at = models.DateTimeField(default=timezone.now)
    finished_at = models.DateTimeField(null=True, blank=True)
    outcome = models.CharField(max_length=40, blank=True)
    provider_status = models.CharField(max_length=80, blank=True)
    http_status = models.PositiveSmallIntegerField(null=True, blank=True)
    retryable = models.BooleanField(default=False)
    error = models.TextField(blank=True)
    response_metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-started_at"]
        constraints = [models.UniqueConstraint(fields=("message", "attempt_number"), name="marketing_attempt_number_unique")]


class ProviderWebhookEvent(models.Model):
    provider = models.CharField(max_length=40)
    event_id = models.CharField(max_length=255)
    event_type = models.CharField(max_length=80)
    received_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    message = models.ForeignKey(OutboundMessage, null=True, blank=True, on_delete=models.SET_NULL, related_name="webhook_events")
    payload = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-received_at"]
        constraints = [models.UniqueConstraint(fields=("provider", "event_id"), name="marketing_provider_event_unique")]
