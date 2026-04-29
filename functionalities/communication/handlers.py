"""
functionalities/communication/handlers.py
Orchestration handlers for communication domain events.
"""


def handle_contact_logged(log, engagement):
    """
    Called after a communication log is saved.
    Placeholder: check if engagement health improved, dismiss related alerts.
    """
    pass


def handle_relationship_went_critical(engagement):
    """
    Triggered when health score drops to 'critical'.
    Placeholder: auto-create alert, notify lead owner.
    """
    pass
