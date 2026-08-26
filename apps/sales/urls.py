from django.urls import path

from . import views

app_name = 'sales'
urlpatterns = [path('', views.sales_orders_view, name='orders')]

