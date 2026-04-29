"""
functionalities/ai/services.py
Phase 3a — Rule-based AI intelligence layer.
All scoring is pure Python arithmetic; no ML dependencies required.
"""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Sum, Q

from apps.engagements.models import Engagement
from apps.clients.models import Client
from apps.alerts.models import Alert
from apps.finance.models import FinancialRecord


# ---------------------------------------------------------------------------
# Thresholds
# ---------------------------------------------------------------------------
CHURN_THRESHOLDS = {
    "low":      0.30,
    "medium":   0.50,
    "high":     0.75,
}

DORMANCY_THRESHOLDS = {
    "low":      0.30,
    "medium":   0.55,
    "high":     0.75,
}


# ---------------------------------------------------------------------------
# Churn-risk scoring
# ---------------------------------------------------------------------------

def _days_since(dt) -> int:
    """Return days elapsed since a date/datetime; 9999 if None."""
    if dt is None:
        return 9999
    if hasattr(dt, "date"):
        dt = dt.date()
    return (date.today() - dt).days


def compute_churn_risk(engagement: Engagement) -> dict:
    """
    Rule-based churn-risk score for a single Engagement.

    Returns
    -------
    {
        'score': float (0–1),
        'label': 'Low' | 'Medium' | 'High' | 'Critical',
        'recommendation': str,
    }
    """
    score = 0.0

    # ── Days since last contact ────────────────────────────────────────────
    days = _days_since(engagement.last_contact)
    if days > 90:
        score += 0.50          # +0.30 base + 0.20 additive
    elif days > 60:
        score += 0.30

    # ── No communication logs ──────────────────────────────────────────────
    log_count = engagement.communication_logs.count()
    if log_count == 0:
        score += 0.20

    # ── High alert count ───────────────────────────────────────────────────
    alert_count = engagement.alerts.filter(is_resolved=False).count()
    if alert_count > 2:
        score += 0.15

    # ── No financial record ────────────────────────────────────────────────
    has_finance = FinancialRecord.objects.filter(engagement=engagement).exists()
    if not has_finance:
        score += 0.15

    # ── Cap at 1.0 ─────────────────────────────────────────────────────────
    score = min(score, 1.0)

    # ── Label + recommendation ─────────────────────────────────────────────
    if score >= CHURN_THRESHOLDS["high"]:
        label = "Critical"
        recommendation = "Immediate escalation required — contact client this week."
    elif score >= CHURN_THRESHOLDS["medium"]:
        label = "High"
        recommendation = "Schedule follow-up within 7 days and review open alerts."
    elif score >= CHURN_THRESHOLDS["low"]:
        label = "Medium"
        recommendation = "Log a communication update and monitor weekly."
    else:
        label = "Low"
        recommendation = "Engagement is healthy — maintain regular cadence."

    return {"score": round(score, 3), "label": label, "recommendation": recommendation}


# ---------------------------------------------------------------------------
# Dormancy-risk scoring
# ---------------------------------------------------------------------------

def compute_dormancy_risk(client: Client) -> dict:
    """
    Rule-based dormancy-risk score for a single Client.

    Returns
    -------
    {
        'score': float (0–1),
        'label': 'Low' | 'Medium' | 'High' | 'Critical',
        'recommended_action': str,
    }
    """
    score = 0.0

    engagements = list(client.engagements.all())

    # ── No engagements at all ──────────────────────────────────────────────
    if not engagements:
        score += 0.50

    else:
        # ── All engagements closed/lost ────────────────────────────────────
        active_statuses = {"active", "pending", "on_hold"}
        active_count = sum(1 for e in engagements if e.status in active_statuses)
        if active_count == 0:
            score += 0.30

        # ── Most recent engagement old ─────────────────────────────────────
        last_dates = [e.last_contact for e in engagements if e.last_contact]
        if last_dates:
            most_recent = max(last_dates)
            days = _days_since(most_recent)
            if days > 180:
                score += 0.35
            elif days > 90:
                score += 0.20

    # ── No unresolved alerts (neutral — absence scores slightly higher) ────
    # Having active alerts means someone is watching; no alerts on dormant = worse
    has_active_alert = Alert.objects.filter(
        client=client, is_resolved=False
    ).exists()
    if not has_active_alert and not engagements:
        score += 0.15

    score = min(score, 1.0)

    if score >= DORMANCY_THRESHOLDS["high"]:
        label = "Critical"
        recommended_action = "Re-engagement campaign — assign relationship owner immediately."
    elif score >= DORMANCY_THRESHOLDS["medium"]:
        label = "High"
        recommended_action = "Schedule re-engagement call within two weeks."
    elif score >= DORMANCY_THRESHOLDS["low"]:
        label = "Medium"
        recommended_action = "Review client profile and recent activity."
    else:
        label = "Low"
        recommended_action = "Client appears active — no immediate action needed."

    return {"score": round(score, 3), "label": label, "recommended_action": recommended_action}


# ---------------------------------------------------------------------------
# Revenue forecast
# ---------------------------------------------------------------------------

def compute_revenue_forecast() -> dict:
    """
    Simple forward extrapolation from pipeline FinancialRecords.

    Method: take all open-pipeline amounts, weight by proximity to expected
    close (based on engagement updated_at as proxy), project into 30/60/90 day
    windows.  Missing close dates default to 60 days out.
    """
    pipeline_records = (
        FinancialRecord.objects
        .filter(record_type="pipeline")
        .select_related("engagement")
    )

    today = date.today()
    forecast = {"30d": Decimal("0"), "60d": Decimal("0"), "90d": Decimal("0")}
    by_centre: dict[str, Decimal] = {}

    for rec in pipeline_records:
        eng = rec.engagement
        if eng is None:
            continue

        # Proxy close date: last updated + 60 days (configurable)
        close_date = eng.updated_at.date() + timedelta(days=60) if eng.updated_at else today + timedelta(days=60)
        delta = (close_date - today).days

        centre_name = eng.centre.name if eng.centre else "Unassigned"
        by_centre.setdefault(centre_name, Decimal("0"))

        if delta <= 30:
            forecast["30d"] += rec.amount
            by_centre[centre_name] += rec.amount
        if delta <= 60:
            forecast["60d"] += rec.amount
        if delta <= 90:
            forecast["90d"] += rec.amount

    by_centre_list = [
        {"centre": k, "amount": float(v)}
        for k, v in sorted(by_centre.items(), key=lambda x: x[1], reverse=True)
    ]

    return {
        "forecast_30d": float(forecast["30d"]),
        "forecast_60d": float(forecast["60d"]),
        "forecast_90d": float(forecast["90d"]),
        "by_centre": by_centre_list,
    }


# ---------------------------------------------------------------------------
# Engagement intensity score (0–100)
# ---------------------------------------------------------------------------

def compute_intensity_score(client: Client) -> int:
    """
    Aggregate engagement intensity for a client (0 = cold, 100 = very active).
    Factors: number of active engagements, log frequency, recent contact.
    """
    engagements = list(client.engagements.all())
    if not engagements:
        return 0

    active = [e for e in engagements if e.status in {"active", "pending"}]
    score = min(len(active) * 15, 40)  # up to 40 pts for active engagements

    # Recent contact
    last_dates = [e.last_contact for e in engagements if e.last_contact]
    if last_dates:
        days = _days_since(max(last_dates))
        if days <= 14:
            score += 35
        elif days <= 30:
            score += 25
        elif days <= 60:
            score += 10

    # Communication log volume (all engagements)
    from apps.communication.models import CommunicationLog
    log_count = CommunicationLog.objects.filter(engagement__client=client).count()
    score += min(log_count * 3, 25)  # up to 25 pts

    return min(score, 100)


# ---------------------------------------------------------------------------
# AI alert pipeline
# ---------------------------------------------------------------------------

def run_ai_alert_pipeline() -> dict:
    """
    Scan all active engagements and clients; create Alert records for
    high/critical risks that don't already have an unresolved AI alert.

    Returns a summary dict: { 'churn_created': int, 'dormancy_created': int }
    """
    churn_created = 0
    dormancy_created = 0

    # ── Churn risk — active engagements ────────────────────────────────────
    active_engagements = Engagement.objects.filter(
        status__in=["active", "pending", "on_hold"]
    ).select_related("client", "centre")

    for eng in active_engagements:
        risk = compute_churn_risk(eng)
        if risk["label"] in ("High", "Critical"):
            already_exists = Alert.objects.filter(
                engagement=eng,
                alert_type="no_contact",
                is_resolved=False,
                title__startswith="[AI]",
            ).exists()
            if not already_exists:
                severity = "critical" if risk["label"] == "Critical" else "high"
                Alert.objects.create(
                    title=f"[AI] Churn Risk — {eng.title[:60]}",
                    description=(
                        f"Churn risk score: {risk['score']:.0%}. "
                        f"{risk['recommendation']}"
                    ),
                    alert_type="no_contact",
                    severity=severity,
                    engagement=eng,
                    client=eng.client,
                )
                churn_created += 1

    # ── Dormancy risk — all clients ────────────────────────────────────────
    for client in Client.objects.all():
        risk = compute_dormancy_risk(client)
        if risk["label"] in ("High", "Critical"):
            already_exists = Alert.objects.filter(
                client=client,
                alert_type="dormant",
                is_resolved=False,
                title__startswith="[AI]",
            ).exists()
            if not already_exists:
                severity = "critical" if risk["label"] == "Critical" else "high"
                Alert.objects.create(
                    title=f"[AI] Dormant Client — {client.name[:60]}",
                    description=(
                        f"Dormancy risk score: {risk['score']:.0%}. "
                        f"{risk['recommended_action']}"
                    ),
                    alert_type="dormant",
                    severity=severity,
                    client=client,
                )
                dormancy_created += 1

    return {"churn_created": churn_created, "dormancy_created": dormancy_created}


# ---------------------------------------------------------------------------
# Aggregated context for the AI Insights view
# ---------------------------------------------------------------------------

def get_ai_insights_context() -> dict:
    """
    Single-call aggregator consumed by apps/ai/views.py.
    Computes all AI metrics and returns a context dict ready for the template.
    """
    # Top churn-risk engagements
    active_engagements = list(
        Engagement.objects.filter(status__in=["active", "pending", "on_hold"])
        .select_related("client", "centre", "lead_owner")
    )
    churn_scores = [
        {"engagement": e, **compute_churn_risk(e)}
        for e in active_engagements
    ]
    churn_scores.sort(key=lambda x: x["score"], reverse=True)
    top_churn = churn_scores[:10]

    # Summary stats
    avg_churn = (
        sum(r["score"] for r in churn_scores) / len(churn_scores)
        if churn_scores else 0.0
    )
    at_risk_count = sum(1 for r in churn_scores if r["label"] in ("High", "Critical"))

    # Top dormancy-risk clients
    all_clients = list(Client.objects.prefetch_related("engagements"))
    dormancy_scores = [
        {"client": c, **compute_dormancy_risk(c)}
        for c in all_clients
    ]
    dormancy_scores.sort(key=lambda x: x["score"], reverse=True)
    top_dormancy = dormancy_scores[:10]
    dormant_count = sum(1 for r in dormancy_scores if r["label"] in ("High", "Critical"))

    # Revenue forecast
    forecast = compute_revenue_forecast()

    return {
        "top_churn": top_churn,
        "avg_churn_score": round(avg_churn * 100, 1),
        "at_risk_count": at_risk_count,
        "top_dormancy": top_dormancy,
        "dormant_count": dormant_count,
        "forecast": forecast,
        "total_active_engagements": len(active_engagements),
        "total_clients": len(all_clients),
    }


# ---------------------------------------------------------------------------
# ML training-readiness check
# ---------------------------------------------------------------------------

_MIN_LABELLED_TOTAL   = 100   # total closed/lost engagements
_MIN_POSITIVE_CLASS   = 30    # 'lost' examples — need both classes
_MIN_BALANCE_RATIO    = 0.10  # lost must be ≥10% of labelled total
_MIN_FEATURE_COVERAGE = 0.70  # ≥70% of labelled rows must have last_contact set


def check_training_readiness() -> dict:
    """
    Inspect the database and report whether there is sufficient labelled data
    to train a churn-prediction ML model.

    Returns
    -------
    {
        ready        (bool)       — True only if ALL hard requirements pass
        hard_passed  (bool)
        soft_passed  (bool)
        checks       (list[dict]) — one entry per check
        summary      (str)        — human-readable verdict
        failed_hard  (list[str])
        failed_soft  (list[str])
    }
    """
    from apps.communication.models import CommunicationLog

    checks = []

    labelled_qs = Engagement.objects.filter(status__in=["lost", "closed"])
    labelled_total = labelled_qs.count()

    # ── 1. Total labelled outcomes (HARD) ─────────────────────────────────
    checks.append({
        "name": "Labelled outcomes (closed + lost engagements)",
        "value": labelled_total,
        "required": _MIN_LABELLED_TOTAL,
        "passed": labelled_total >= _MIN_LABELLED_TOTAL,
        "hard": True,
        "note": (
            f"Need {_MIN_LABELLED_TOTAL - labelled_total} more terminal engagements."
            if labelled_total < _MIN_LABELLED_TOTAL
            else "Sufficient labelled outcomes."
        ),
    })

    # ── 2. Positive-class (churn) examples (HARD) ─────────────────────────
    churn_count = Engagement.objects.filter(status="lost").count()
    checks.append({
        "name": "Churn examples (lost engagements)",
        "value": churn_count,
        "required": _MIN_POSITIVE_CLASS,
        "passed": churn_count >= _MIN_POSITIVE_CLASS,
        "hard": True,
        "note": (
            f"Need {_MIN_POSITIVE_CLASS - churn_count} more 'lost' engagements."
            if churn_count < _MIN_POSITIVE_CLASS
            else "Sufficient churn examples."
        ),
    })

    # ── 3. Class balance (HARD) ────────────────────────────────────────────
    balance_ratio = (churn_count / labelled_total) if labelled_total > 0 else 0.0
    checks.append({
        "name": "Class balance ratio (lost / total labelled)",
        "value": round(balance_ratio, 3),
        "required": _MIN_BALANCE_RATIO,
        "passed": balance_ratio >= _MIN_BALANCE_RATIO,
        "hard": True,
        "note": (
            "Positive class too rare — model will be biased toward majority class."
            if balance_ratio < _MIN_BALANCE_RATIO
            else f"Balance ratio {balance_ratio:.0%} is acceptable."
        ),
    })

    # ── 4. last_contact coverage (SOFT) ───────────────────────────────────
    labelled_with_contact = labelled_qs.filter(last_contact__isnull=False).count()
    coverage = (labelled_with_contact / labelled_total) if labelled_total > 0 else 0.0
    checks.append({
        "name": "Feature coverage — last_contact populated",
        "value": round(coverage, 3),
        "required": _MIN_FEATURE_COVERAGE,
        "passed": coverage >= _MIN_FEATURE_COVERAGE,
        "hard": False,
        "note": (
            f"{labelled_total - labelled_with_contact} labelled rows missing last_contact."
            if coverage < _MIN_FEATURE_COVERAGE
            else "last_contact field coverage is good."
        ),
    })

    # ── 5. Communication log coverage (SOFT) ──────────────────────────────
    engagements_with_logs = (
        CommunicationLog.objects
        .filter(engagement__status__in=["lost", "closed"])
        .values("engagement").distinct().count()
    )
    log_coverage = (engagements_with_logs / labelled_total) if labelled_total > 0 else 0.0
    checks.append({
        "name": "Communication log coverage",
        "value": round(log_coverage, 3),
        "required": _MIN_FEATURE_COVERAGE,
        "passed": log_coverage >= _MIN_FEATURE_COVERAGE,
        "hard": False,
        "note": f"{log_coverage:.0%} of labelled engagements have communication logs.",
    })

    # ── 6. Financial record coverage (SOFT) ───────────────────────────────
    engagements_with_finance = (
        FinancialRecord.objects
        .filter(engagement__status__in=["lost", "closed"])
        .values("engagement").distinct().count()
    )
    finance_coverage = (engagements_with_finance / labelled_total) if labelled_total > 0 else 0.0
    checks.append({
        "name": "Financial record coverage",
        "value": round(finance_coverage, 3),
        "required": _MIN_FEATURE_COVERAGE,
        "passed": finance_coverage >= _MIN_FEATURE_COVERAGE,
        "hard": False,
        "note": f"{finance_coverage:.0%} of labelled engagements have financial records.",
    })

    # ── Verdict ────────────────────────────────────────────────────────────
    hard_passed = all(c["passed"] for c in checks if c["hard"])
    soft_passed = all(c["passed"] for c in checks if not c["hard"])

    if hard_passed and soft_passed:
        summary = "Database is ready for ML model training."
    elif hard_passed:
        summary = (
            "Hard requirements met — training is possible but feature quality is low. "
            "Improve data completeness for better model accuracy."
        )
    else:
        remaining = max(0, _MIN_LABELLED_TOTAL - labelled_total)
        summary = (
            f"Not ready. {labelled_total}/{_MIN_LABELLED_TOTAL} labelled engagements collected. "
            f"Continue using rule-based scoring for approximately {remaining} more closed/lost outcomes."
        )

    return {
        "ready": hard_passed,
        "hard_passed": hard_passed,
        "soft_passed": soft_passed,
        "checks": checks,
        "summary": summary,
        "labelled_total": labelled_total,
        "labelled_needed": _MIN_LABELLED_TOTAL,
        "progress_pct": min(100, round(labelled_total / _MIN_LABELLED_TOTAL * 100)),
        "failed_hard": [c["name"] for c in checks if c["hard"] and not c["passed"]],
        "failed_soft": [c["name"] for c in checks if not c["hard"] and not c["passed"]],
    }
