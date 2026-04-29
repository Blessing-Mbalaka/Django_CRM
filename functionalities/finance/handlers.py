"""
functionalities/finance/handlers.py
Orchestration handlers for financial domain events.
"""


def handle_record_marked_paid(record, user):
    """
    Triggered when a financial record is marked as paid.
    Placeholder: update engagement revenue totals, notify director.
    """
    pass


def handle_overdue_invoice_detected(record):
    """
    Triggered by alert pipeline when a record is unpaid past due date.
    Placeholder: create Alert, send notification.
    """
    pass
