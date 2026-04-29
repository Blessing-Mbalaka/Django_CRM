from django.urls import path
from . import views

app_name = "ai"

urlpatterns = [
    path("", views.insights_view, name="insights"),
]
