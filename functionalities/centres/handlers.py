"""
functionalities/centres/handlers.py
Orchestration handlers for centre domain events.
"""


def handle_centre_created(centre, user):
    """Post-creation hook. Placeholder for audit logging / notifications."""
    pass


def handle_centre_deactivated(centre, user):
    """
    Called when a centre is set to inactive.
    Could trigger reassignment workflows for linked staff/engagements.
    """
    pass
