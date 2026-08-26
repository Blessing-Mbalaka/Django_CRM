from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.api.permissions import IsCEODirectorOrAdmin
from django.utils import timezone

from functionalities.accounting.reconciliation import reconcile_statement_line, reconciliation_candidates, unreconcile_statement_line
from functionalities.accounting.reports import balance_sheet, income_statement, trial_balance
from functionalities.accounting.services import post_entry, reverse_entry
from .models import Account, AccountingPeriod, BankStatement, BankStatementLine, JournalEntry, JournalLine
from .serializers import AccountSerializer, AccountingPeriodSerializer, BankStatementLineSerializer, BankStatementSerializer, JournalEntrySerializer, ReconciliationCandidateSerializer


class ManagementWriteViewSet(viewsets.ModelViewSet):
    def get_permissions(self):
        return [IsAuthenticated()] if self.action in ('list', 'retrieve') else [IsCEODirectorOrAdmin()]


class AccountViewSet(ManagementWriteViewSet):
    serializer_class = AccountSerializer
    queryset = Account.objects.all()


class AccountingPeriodViewSet(ManagementWriteViewSet):
    serializer_class = AccountingPeriodSerializer
    queryset = AccountingPeriod.objects.all()


class JournalEntryViewSet(ManagementWriteViewSet):
    serializer_class = JournalEntrySerializer
    queryset = JournalEntry.objects.select_related('created_by').prefetch_related('lines__account')
    http_method_names = ['get', 'post', 'head', 'options']

    @action(detail=True, methods=['post'])
    def post(self, request, pk=None):
        try:
            entry = post_entry(entry=self.get_object())
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc
        return Response(self.get_serializer(entry).data)

    @action(detail=True, methods=['post'])
    def reverse(self, request, pk=None):
        if not request.data.get('date'):
            raise serializers.ValidationError({'date': 'Reversal date is required.'})
        try:
            reversal = reverse_entry(entry=self.get_object(), reversal_date=request.data['date'], description=request.data.get('description', ''), user=request.user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc
        return Response(self.get_serializer(reversal).data)


class BankStatementViewSet(viewsets.ModelViewSet):
    serializer_class = BankStatementSerializer
    queryset = BankStatement.objects.select_related('bank_account', 'created_by').prefetch_related('lines__matched_journal_line__entry')
    http_method_names = ['get', 'post', 'head', 'options']

    def get_permissions(self):
        return [IsAuthenticated()] if self.action in ('list', 'retrieve') else [IsCEODirectorOrAdmin()]


class BankStatementLineViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = BankStatementLineSerializer
    queryset = BankStatementLine.objects.select_related('statement__bank_account', 'matched_journal_line__entry', 'reconciled_by')

    def get_permissions(self):
        return [IsAuthenticated()] if self.action in ('list', 'retrieve', 'candidates') else [IsCEODirectorOrAdmin()]

    @action(detail=True, methods=['get'])
    def candidates(self, request, pk=None):
        return Response(ReconciliationCandidateSerializer(reconciliation_candidates(statement_line=self.get_object()), many=True).data)

    @action(detail=True, methods=['post'])
    def reconcile(self, request, pk=None):
        journal_line_field = serializers.IntegerField(min_value=1)
        try:
            journal_line_id = journal_line_field.run_validation(request.data.get('journal_line'))
        except serializers.ValidationError as exc:
            raise serializers.ValidationError({'journal_line': exc.detail}) from exc
        try:
            line = reconcile_statement_line(statement_line=self.get_object(), journal_line=JournalLine.objects.get(pk=journal_line_id), user=request.user)
        except JournalLine.DoesNotExist as exc:
            raise serializers.ValidationError({'journal_line': 'Journal line was not found.'}) from exc
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc
        return Response(self.get_serializer(line).data)

    @action(detail=True, methods=['post'])
    def unreconcile(self, request, pk=None):
        try:
            line = unreconcile_statement_line(statement_line=self.get_object())
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc
        return Response(self.get_serializer(line).data)


def report_response(builder, **kwargs):
    try:
        return Response(builder(**kwargs))
    except DjangoValidationError as exc:
        detail = exc.message_dict if hasattr(exc, 'message_dict') else exc.messages
        raise serializers.ValidationError(detail) from exc


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def trial_balance_report(request):
    return report_response(trial_balance, as_of=request.query_params.get('as_of') or timezone.localdate())


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def income_statement_report(request):
    today = timezone.localdate()
    return report_response(income_statement, start_date=request.query_params.get('start_date') or today.replace(month=1, day=1), end_date=request.query_params.get('end_date') or today)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def balance_sheet_report(request):
    return report_response(balance_sheet, as_of=request.query_params.get('as_of') or timezone.localdate())
