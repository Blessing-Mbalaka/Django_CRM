from django.urls import path

from . import views
from . import webhook_views

app_name = "marketing"

urlpatterns = [
    path("", views.index, name="index"),
    path("webhooks/twilio/sms/", webhook_views.twilio_status_webhook, name="twilio-status-webhook"),
    path("webhooks/meta/", webhook_views.meta_webhook, name="meta-webhook"),
]
