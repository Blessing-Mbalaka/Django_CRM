from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.api.permissions import IsDeanDirectorOrAdmin
from functionalities.accounting.services import post_entry, reverse_entry
from .models import Account, AccountingPeriod, JournalEntry
from .serializers import AccountSerializer, AccountingPeriodSerializer, JournalEntrySerializer


class ManagementWriteViewSet(viewsets.ModelViewSet):
    def get_permissions(self):
        return [IsAuthenticated()] if self.action in ('list', 'retrieve') else [IsDeanDirectorOrAdmin()]


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
