from django.urls import path

from . import views

app_name = 'purchasing'
urlpatterns = [path('', views.purchase_orders_view, name='orders')]

