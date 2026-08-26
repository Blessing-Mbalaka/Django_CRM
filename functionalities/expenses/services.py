from django.db import transaction

from apps.expenses.models import Expense, ExpenseApproval


@transaction.atomic
def submit_expense(*, expense):
    expense = Expense.objects.select_for_update().get(pk=expense.pk)
    if expense.status not in (Expense.Status.DRAFT, Expense.Status.REJECTED):
        raise ValueError('Only draft or rejected expenses can be submitted.')
    expense.status = Expense.Status.SUBMITTED
    expense.save(update_fields=['status', 'updated_at'])
    return expense


@transaction.atomic
def decide_expense(*, expense, decision, user, comment=''):
    expense = Expense.objects.select_for_update().get(pk=expense.pk)
    if expense.status != Expense.Status.SUBMITTED:
        raise ValueError('Only submitted expenses can be approved or rejected.')
    if decision not in ExpenseApproval.Decision.values:
        raise ValueError('Invalid expense decision.')
    ExpenseApproval.objects.create(expense=expense, decision=decision, comment=comment, decided_by=user)
    expense.status = decision
    expense.save(update_fields=['status', 'updated_at'])
    if decision == ExpenseApproval.Decision.APPROVED:
        from functionalities.accounting.posting import post_expense
        post_expense(expense, user)
    return expense
