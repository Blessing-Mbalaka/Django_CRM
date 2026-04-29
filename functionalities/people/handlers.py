"""
functionalities/people/handlers.py
Orchestration handlers for people/staff domain events.
"""


def handle_staff_member_added(user, centre, created_by):
    """
    Called after a new staff member is created.
    Placeholder: send welcome email, update centre staff count cache.
    """
    pass


def handle_staff_member_deactivated(user, deactivated_by):
    """
    Called when a staff member is deactivated.
    Placeholder: reassign open engagements, revoke tokens.
    """
    pass
