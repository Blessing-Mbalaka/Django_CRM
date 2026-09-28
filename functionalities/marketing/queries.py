from django.db.models import Count

from apps.marketing.models import MarketingActivity, MarketingAdvert, MarketingCampaign, MarketingContent, MarketingLead, OutboundMessage


def marketing_summary():
    campaign_statuses = {row["status"]: row["count"] for row in MarketingCampaign.objects.values("status").annotate(count=Count("id"))}
    lead_statuses = {row["status"]: row["count"] for row in MarketingLead.objects.values("status").annotate(count=Count("id"))}
    delivery_statuses = {row["status"]: row["count"] for row in OutboundMessage.objects.values("status").annotate(count=Count("id"))}
    return {
        "campaigns": {"total": MarketingCampaign.objects.count(), **campaign_statuses},
        "leads": {"total": MarketingLead.objects.count(), **lead_statuses},
        "delivery": {"total": OutboundMessage.objects.count(), **delivery_statuses},
        "content": MarketingContent.objects.count(),
        "adverts": MarketingAdvert.objects.count(),
    }


def marketing_calendar():
    results = []
    for campaign in MarketingCampaign.objects.all():
        results.append({"source": "campaign", "id": campaign.pk, "title": campaign.name, "starts_at": campaign.start_date.isoformat(), "status": campaign.status})
    for advert in MarketingAdvert.objects.all():
        results.append({"source": "advert", "id": advert.pk, "title": advert.name, "starts_at": advert.start_date.isoformat(), "status": advert.status})
    for content in MarketingContent.objects.exclude(scheduled_at=None):
        results.append({"source": "content", "id": content.pk, "title": content.title, "starts_at": content.scheduled_at.isoformat(), "status": content.status})
    for activity in MarketingActivity.objects.all():
        results.append({"source": "activity", "id": activity.pk, "title": activity.name, "starts_at": activity.starts_at.isoformat(), "type": activity.activity_type})
    return {"results": sorted(results, key=lambda item: (item["starts_at"], item["source"], item["id"]))}
