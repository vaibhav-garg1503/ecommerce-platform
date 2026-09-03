from django.urls import path
from apps.payments import views

app_name = 'payments'

urlpatterns = [
    path('<str:order_number>/', views.payment_page_view, name='payment_page'),
    path('callback/', views.payment_callback_view, name='payment_callback'),
    path('webhook/', views.payment_webhook_view, name='payment_webhook'),
    path('cod/<str:order_number>/', views.cod_place_order_view, name='cod_place_order'),
]
