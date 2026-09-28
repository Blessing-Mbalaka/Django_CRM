from django.db import transaction
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.api.permissions import IsCEODirectorOrAdmin
from apps.clients.models import Client
from functionalities.marketing.analytics import marketing_analytics
from functionalities.marketing.dispatch import cancel_message, dispatch_message, queue_message, retry_message
from functionalities.marketing.providers.status import ProviderState, provider_status
from functionalities.marketing.queries import marketing_calendar, marketing_summary

from .models import BrandKit, MarketingActivity, MarketingAdvert, MarketingCampaign, MarketingContact, MarketingContent, MarketingLead, MarketingMetric, OutboundMessage
from .serializers import BrandKitSerializer, MarketingActivitySerializer, MarketingAdvertSerializer, MarketingCampaignSerializer, MarketingContactSerializer, MarketingContentSerializer, MarketingLeadSerializer, MarketingMetricSerializer, OutboundMessageSerializer


class ManagementWriteViewSet(viewsets.ModelViewSet):
    def get_permissions(self):
        return [IsAuthenticated()] if self.action in ("list", "retrieve") else [IsCEODirectorOrAdmin()]

    def get_queryset(self):
        queryset = super().get_queryset()
        if status_value := self.request.query_params.get("status"):
            if any(field.name == "status" for field in queryset.model._meta.fields):
                queryset = queryset.filter(status=status_value)
        if campaign := self.request.query_params.get("campaign"):
            if any(field.name == "campaign" for field in queryset.model._meta.fields):
                queryset = queryset.filter(campaign_id=campaign)
        return queryset


class MarketingCampaignViewSet(ManagementWriteViewSet):
    queryset = MarketingCampaign.objects.select_related("owner")
    serializer_class = MarketingCampaignSerializer
    def perform_create(self, serializer): serializer.save(owner=self.request.user)


class MarketingAdvertViewSet(ManagementWriteViewSet):
    queryset = MarketingAdvert.objects.select_related("campaign")
    serializer_class = MarketingAdvertSerializer


class MarketingContentViewSet(ManagementWriteViewSet):
    queryset = MarketingContent.objects.select_related("campaign")
    serializer_class = MarketingContentSerializer


class MarketingContactViewSet(ManagementWriteViewSet):
    serializer_class = MarketingContactSerializer
    queryset = MarketingContact.objects.select_related("client")
    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset if self.request.query_params.get("include_inactive") == "1" else queryset.filter(is_active=True)


class MarketingLeadViewSet(ManagementWriteViewSet):
    queryset = MarketingLead.objects.select_related("contact", "campaign", "owner", "client")
    serializer_class = MarketingLeadSerializer
    def perform_create(self, serializer): serializer.save(owner=self.request.user)

    @action(detail=True, methods=["post"], url_path="convert-to-client", permission_classes=[IsCEODirectorOrAdmin])
    @transaction.atomic
    def convert_to_client(self, request, pk=None):
        lead = self.get_object()
        if lead.client_id:
            client = lead.client
        elif lead.contact and lead.contact.client_id:
            client = lead.contact.client
        else:
            name = lead.contact.name if lead.contact else f"Marketing lead {lead.pk}"
            client = Client.objects.filter(name__iexact=name).first() or Client.objects.create(name=name)
        lead.client = client
        lead.status = MarketingLead.Status.CONVERTED
        lead.save(update_fields=["client", "status", "updated_at"])
        if lead.contact and not lead.contact.client_id:
            lead.contact.client = client
            lead.contact.save(update_fields=["client", "updated_at"])
        return Response(self.get_serializer(lead).data)


class MarketingActivityViewSet(ManagementWriteViewSet):
    queryset = MarketingActivity.objects.select_related("campaign", "advert", "content")
    serializer_class = MarketingActivitySerializer


class MarketingMetricViewSet(ManagementWriteViewSet):
    queryset = MarketingMetric.objects.select_related("campaign", "advert")
    serializer_class = MarketingMetricSerializer


class BrandKitViewSet(ManagementWriteViewSet):
    serializer_class = BrandKitSerializer
    http_method_names = ["get", "put", "patch", "head", "options"]
    def get_queryset(self):
        BrandKit.load()
        return BrandKit.objects.filter(pk=1).order_by("pk")


class OutboundMessageViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = OutboundMessage.objects.select_related("campaign", "content", "contact", "created_by")
    serializer_class = OutboundMessageSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=["post"], permission_classes=[IsCEODirectorOrAdmin])
    def retry(self, request, pk=None):
        message = retry_message(message=self.get_object(), actor=request.user)
        message = dispatch_message(message.pk)
        return Response(self.get_serializer(message).data, status=status.HTTP_202_ACCEPTED)

    @action(detail=True, methods=["post"], permission_classes=[IsCEODirectorOrAdmin])
    def cancel(self, request, pk=None):
        return Response(self.get_serializer(cancel_message(message=self.get_object(), actor=request.user)).data)


class MarketingWorkspaceViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request): return self.summary(request)
    @action(detail=False)
    def summary(self, request): return Response(marketing_summary())
    @action(detail=False)
    def calendar(self, request): return Response(marketing_calendar())
    @action(detail=False)
    def analytics(self, request): return Response(marketing_analytics())

    @action(detail=False, url_path="provider-status")
    def provider_status_action(self, request):
        return Response({name: {"state": item.state.value, "message": item.message, "missing": item.missing} for name, item in provider_status().items()})

    @action(detail=False, methods=["post"], permission_classes=[IsCEODirectorOrAdmin])
    def preview(self, request):
        brand = BrandKit.load()
        return Response({"subject": request.data.get("subject", ""), "text": request.data.get("body", ""), "html": request.data.get("html", ""), "brand": BrandKitSerializer(brand, context={"request": request}).data})

    def _queue(self, request, *, scheduled_at=None):
        contact = MarketingContact.objects.filter(pk=request.data.get("contact")).first() if request.data.get("contact") else None
        campaign = MarketingCampaign.objects.filter(pk=request.data.get("campaign")).first() if request.data.get("campaign") else None
        content = MarketingContent.objects.filter(pk=request.data.get("content")).first() if request.data.get("content") else None
        try:
            return queue_message(
                channel=request.data.get("channel", ""), actor=request.user, contact=contact, campaign=campaign, content=content,
                destination=request.data.get("destination", ""), subject=request.data.get("subject", ""),
                body=request.data.get("body", ""), html=request.data.get("html", ""),
                media_url=request.data.get("media_url", ""), scheduled_at=scheduled_at,
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict if hasattr(exc, "message_dict") else exc.messages) from exc

    @action(detail=False, methods=["post"], permission_classes=[IsCEODirectorOrAdmin])
    def send(self, request):
        provider_name = {"email": "twilio_email", "sms": "twilio_sms", "whatsapp": "meta_whatsapp", "facebook": "meta_facebook", "instagram": "meta_instagram"}.get(request.data.get("channel"))
        status_item = provider_status().get(provider_name)
        if not status_item or status_item.state is not ProviderState.AVAILABLE:
            return Response({"detail": status_item.message if status_item else "Channel unavailable."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        message = self._queue(request)
        dispatch_message(message.pk)
        message.refresh_from_db()
        return Response(OutboundMessageSerializer(message).data, status=status.HTTP_202_ACCEPTED)

    @action(detail=False, methods=["post"], permission_classes=[IsCEODirectorOrAdmin])
    def schedule(self, request):
        value = request.data.get("scheduled_at")
        parsed = serializers.DateTimeField().run_validation(value)
        if parsed <= timezone.now():
            raise serializers.ValidationError({"scheduled_at": "Choose a future date and time."})
        message = self._queue(request, scheduled_at=parsed)
        return Response(OutboundMessageSerializer(message).data, status=status.HTTP_201_CREATED)
