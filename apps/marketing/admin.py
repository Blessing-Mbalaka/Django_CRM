from django.contrib import admin

from .models import (
    BrandKit,
    DeliveryAttempt,
    MarketingActivity,
    MarketingAdvert,
    MarketingCampaign,
    MarketingContact,
    MarketingContent,
    MarketingLead,
    MarketingMetric,
    OutboundMessage,
    ProviderWebhookEvent,
)


@admin.register(MarketingCampaign)
class MarketingCampaignAdmin(admin.ModelAdmin):
    list_display = ("name", "status", "start_date", "end_date", "owner")
    list_filter = ("status",)
    search_fields = ("name", "objective", "target_audience")


@admin.register(MarketingContact)
class MarketingContactAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "mobile_number", "is_active")
    list_filter = ("is_active", "email_consent", "sms_consent", "whatsapp_consent")
    search_fields = ("name", "email", "mobile_number", "whatsapp_number")


@admin.register(OutboundMessage)
class OutboundMessageAdmin(admin.ModelAdmin):
    list_display = ("channel", "destination", "status", "provider", "scheduled_at", "created_at")
    list_filter = ("channel", "status", "provider")
    search_fields = ("destination", "provider_message_id", "subject_snapshot")
    readonly_fields = ("destination", "subject_snapshot", "content_snapshot", "html_snapshot", "media_url_snapshot")


admin.site.register(MarketingAdvert)
admin.site.register(MarketingContent)
admin.site.register(MarketingLead)
admin.site.register(MarketingActivity)
admin.site.register(MarketingMetric)
admin.site.register(BrandKit)
admin.site.register(DeliveryAttempt)
admin.site.register(ProviderWebhookEvent)
