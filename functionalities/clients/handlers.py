"""
functionalities/clients/handlers.py
Orchestration handlers for client domain events.
"""
from . import services


def handle_client_created(client, user):
    """
    Called after a new client is successfully created.
    Placeholder for post-creation side-effects:
    - Audit logging
    - Notification dispatch
    - CRM sync hooks
    """
    pass


def handle_client_deleted(client_name, user):
    """
    Called after a client is deleted.
    Placeholder for cascading clean-up or audit log entries.
    """
    pass
