"""
functionalities/engagements/handlers.py
Orchestration handlers for engagement lifecycle events.
"""


def handle_engagement_created(engagement, user):
    """
    Post-creation hook: alert pipeline, audit log, notification.
    """
    pass


def handle_engagement_status_changed(engagement, old_status, new_status, user):
    """
    Triggered when engagement status transitions.
    E.g. prospect → active could generate a financial record prompt.
    """
    pass


def handle_engagement_closed(engagement, user):
    """
    Triggered when engagement moves to 'closed' or 'lost'.
    Placeholder for archiving, reporting snapshots, etc.
    """
    pass
