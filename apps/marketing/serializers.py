from apps.companies.serializers import CompanyModelSerializer
from decimal import Decimal

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import (
    BrandKit, MarketingActivity, MarketingAdvert, MarketingCampaign, MarketingContact,
    MarketingContent, MarketingLead, MarketingMetric, OutboundMessage,
)


class CleanModelSerializer(CompanyModelSerializer):
    def validate(self, attrs):
        values = {}
        if self.instance:
            for field in self.Meta.model._meta.concrete_fields:
                values[field.name] = getattr(self.instance, field.name)
        values.update(attrs)
        values.pop("id", None)
        candidate = self.Meta.model(**values)
        try:
            candidate.clean()
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict if hasattr(exc, "message_dict") else exc.messages) from exc
        return attrs


class MarketingCampaignSerializer(CleanModelSerializer):
    budget = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=Decimal("0"), required=False)

    class Meta:
        model = MarketingCampaign
        fields = ["id", "name", "objective", "product_service", "target_audience", "target_location", "channels", "start_date", "end_date", "budget", "status", "description", "owner", "created_at", "updated_at"]
        read_only_fields = ["id", "owner", "created_at", "updated_at"]


class MarketingAdvertSerializer(CleanModelSerializer):
    budget = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=Decimal("0"), required=False)
    actual_spend = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=Decimal("0"), required=False)

    class Meta:
        model = MarketingAdvert
        fields = ["id", "campaign", "name", "advertised_subject", "advertising_type", "platform", "audience", "location", "start_date", "end_date", "budget", "actual_spend", "destination_url", "status", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class MarketingContentSerializer(CleanModelSerializer):
    class Meta:
        model = MarketingContent
        fields = ["id", "campaign", "kind", "title", "subject", "heading", "body", "call_to_action", "call_to_action_url", "hashtags", "platform", "template", "image", "scheduled_at", "status", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class MarketingContactSerializer(CleanModelSerializer):
    class Meta:
        model = MarketingContact
        fields = ["id", "name", "email", "mobile_number", "whatsapp_number", "source", "client", "email_consent", "sms_consent", "whatsapp_consent", "email_consented_at", "sms_consented_at", "whatsapp_consented_at", "consent_source", "email_opted_out_at", "sms_opted_out_at", "whatsapp_opted_out_at", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class MarketingLeadSerializer(CleanModelSerializer):
    estimated_value = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=Decimal("0"), required=False)

    class Meta:
        model = MarketingLead
        fields = ["id", "contact", "campaign", "acquisition_source", "received_date", "status", "estimated_value", "notes", "owner", "client", "created_at", "updated_at"]
        read_only_fields = ["id", "owner", "client", "created_at", "updated_at"]


class MarketingActivitySerializer(CleanModelSerializer):
    class Meta:
        model = MarketingActivity
        fields = ["id", "name", "activity_type", "starts_at", "ends_at", "description", "campaign", "advert", "content", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class MarketingMetricSerializer(CleanModelSerializer):
    spend = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=Decimal("0"), required=False)
    attributed_revenue = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=Decimal("0"), required=False)

    class Meta:
        model = MarketingMetric
        fields = ["id", "campaign", "advert", "channel", "reporting_date", "period", "spend", "reach", "responses", "enquiries", "leads", "customers", "attributed_revenue", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class BrandKitSerializer(CleanModelSerializer):
    class Meta:
        model = BrandKit
        fields = ["id", "business_name", "slogan", "logo", "primary_colour", "secondary_colour", "accent_colour", "heading_font", "body_font", "short_description", "long_description", "phone", "whatsapp", "email", "website", "physical_location", "facebook_url", "instagram_url", "linkedin_url", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class OutboundMessageSerializer(CompanyModelSerializer):
    class Meta:
        model = OutboundMessage
        fields = ["id", "channel", "campaign", "content", "contact", "destination", "subject_snapshot", "content_snapshot", "html_snapshot", "media_url_snapshot", "scheduled_at", "status", "provider", "provider_message_id", "accepted_at", "sent_at", "delivered_at", "read_at", "failed_at", "attempt_count", "last_error", "created_by", "created_at", "updated_at"]
        read_only_fields = fields
