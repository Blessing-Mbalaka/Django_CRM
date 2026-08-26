from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.api.permissions import IsDeanDirectorOrAdmin
from functionalities.expenses.services import decide_expense, submit_expense
from .models import Expense, ExpenseCategory
from .serializers import ExpenseCategorySerializer, ExpenseSerializer


class ExpenseCategoryViewSet(viewsets.ModelViewSet):
    serializer_class = ExpenseCategorySerializer
    queryset = ExpenseCategory.objects.all()

    def get_permissions(self):
        return [IsDeanDirectorOrAdmin()] if self.action not in ('list', 'retrieve') else [IsAuthenticated()]


class ExpenseViewSet(viewsets.ModelViewSet):
    serializer_class = ExpenseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Expense.objects.select_related('category', 'submitted_by', 'client', 'engagement', 'receipt_document').prefetch_related('approvals')
        user = self.request.user
        if not (user.is_superuser or user.role in ('dean', 'director', 'admin')):
            qs = qs.filter(submitted_by=user)
        if status_value := self.request.query_params.get('status'):
            qs = qs.filter(status=status_value)
        return qs

    def perform_create(self, serializer):
        serializer.save(submitted_by=self.request.user)

    def perform_destroy(self, instance):
        if instance.status not in (Expense.Status.DRAFT, Expense.Status.REJECTED):
            raise serializers.ValidationError('Only draft or rejected expenses can be deleted.')
        instance.delete()

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        try:
            expense = submit_expense(expense=self.get_object())
        except ValueError as exc:
            raise serializers.ValidationError({'expense': str(exc)})
        return Response(self.get_serializer(expense).data)

    def _decide(self, request, decision):
        if not (request.user.is_superuser or request.user.role in ('dean', 'director', 'admin')):
            return Response({'detail': 'Management approval is required.'}, status=status.HTTP_403_FORBIDDEN)
        try:
            expense = decide_expense(expense=self.get_object(), decision=decision, user=request.user, comment=request.data.get('comment', ''))
        except ValueError as exc:
            raise serializers.ValidationError({'expense': str(exc)})
        return Response(self.get_serializer(expense).data)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        return self._decide(request, Expense.Status.APPROVED)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        return self._decide(request, Expense.Status.REJECTED)
