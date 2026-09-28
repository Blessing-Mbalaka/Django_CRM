from django.db.models import Sum

from apps.marketing.models import MarketingMetric


def marketing_analytics():
    aggregates = MarketingMetric.objects.aggregate(
        spend=Sum("spend"), reach=Sum("reach"), responses=Sum("responses"), enquiries=Sum("enquiries"),
        leads=Sum("leads"), customers=Sum("customers"), revenue=Sum("attributed_revenue"),
    )
    available = aggregates["spend"] is not None
    if not available:
        return {"available": False, "totals": None, "cost_per_enquiry": None, "roas": None, "channels": []}
    totals = {key: float(value) if key in {"spend", "revenue"} else int(value or 0) for key, value in aggregates.items()}
    spend = totals["spend"]
    enquiries = totals["enquiries"]
    channels = list(MarketingMetric.objects.values("channel").annotate(spend=Sum("spend"), reach=Sum("reach"), leads=Sum("leads"), revenue=Sum("attributed_revenue")).order_by("channel"))
    for row in channels:
        row["spend"] = float(row["spend"] or 0)
        row["revenue"] = float(row["revenue"] or 0)
    return {
        "available": True,
        "totals": totals,
        "cost_per_enquiry": round(spend / enquiries, 2) if enquiries else None,
        "roas": round(totals["revenue"] / spend, 2) if spend else None,
        "channels": channels,
    }
