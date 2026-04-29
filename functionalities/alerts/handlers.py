"""
functionalities/alerts/handlers.py
Orchestration handlers for alert lifecycle events.
"""


def handle_alert_created(alert):
    """Post-creation hook. Placeholder: push notification, email digest."""
    pass


def handle_alert_resolved(alert, user):
    """Called when an alert is resolved. Placeholder: audit log."""
    pass


def handle_pipeline_run_complete(summary):
    """
    Called after run_alert_pipeline() completes.
    summary: {no_contact: int, payment_due: int, overlap: int}
    Placeholder: log results, send digest to Dean.
    """
    pass
