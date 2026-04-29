from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from functionalities.ai.services import get_ai_insights_context, run_ai_alert_pipeline, check_training_readiness


@login_required
def insights_view(request):
    """Render the AI Insights dashboard page."""
    if request.method == "POST" and request.POST.get("action") == "run_pipeline":
        summary = run_ai_alert_pipeline()
        run_msg = (
            f"AI pipeline complete — {summary['churn_created']} churn alert(s) "
            f"and {summary['dormancy_created']} dormancy alert(s) created."
        )
    else:
        run_msg = None

    context = get_ai_insights_context()
    context["run_msg"] = run_msg
    context["readiness"] = check_training_readiness()
    return render(request, "ai/insights.html", context)
