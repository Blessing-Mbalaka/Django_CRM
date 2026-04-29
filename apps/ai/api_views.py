from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from functionalities.ai.services import (
    get_ai_insights_context,
    run_ai_alert_pipeline,
    check_training_readiness,
)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def ai_insights(request):
    """
    GET /api/ai/insights/
    Returns full AI insights payload as JSON.
    """
    ctx = get_ai_insights_context()

    # Serialise ORM objects → dicts for JSON response
    payload = {
        "summary": {
            "avg_churn_score": ctx["avg_churn_score"],
            "at_risk_count": ctx["at_risk_count"],
            "dormant_count": ctx["dormant_count"],
            "total_active_engagements": ctx["total_active_engagements"],
            "total_clients": ctx["total_clients"],
        },
        "top_churn_risks": [
            {
                "engagement_id": r["engagement"].pk,
                "engagement_title": r["engagement"].title,
                "client": r["engagement"].client.name if r["engagement"].client else None,
                "score": r["score"],
                "label": r["label"],
                "recommendation": r["recommendation"],
            }
            for r in ctx["top_churn"]
        ],
        "top_dormancy_risks": [
            {
                "client_id": r["client"].pk,
                "client_name": r["client"].name,
                "score": r["score"],
                "label": r["label"],
                "recommended_action": r["recommended_action"],
            }
            for r in ctx["top_dormancy"]
        ],
        "revenue_forecast": ctx["forecast"],
    }
    return Response(payload)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def training_readiness(request):
    """
    GET /api/ai/readiness/
    Reports whether the database has sufficient data to train an ML churn model.
    """
    result = check_training_readiness()
    return Response(result)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def run_pipeline(request):
    """
    POST /api/ai/run-pipeline/
    Triggers the AI alert pipeline and returns a summary.
    """
    summary = run_ai_alert_pipeline()
    return Response({"status": "ok", **summary})
