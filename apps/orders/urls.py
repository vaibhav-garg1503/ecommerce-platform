from django.urls import path
from apps.orders import views

app_name = 'orders'

urlpatterns = [
    path('checkout/', views.checkout_view, name='checkout'),
    path('confirm/<str:order_number>/', views.order_confirm_view, name='order_confirm'),
    path('coupon/apply/', views.apply_coupon_view, name='apply_coupon'),
    path('', views.order_list_view, name='order_list'),
    path('<str:order_number>/', views.order_detail_view, name='order_detail'),
    path('<str:order_number>/invoice/', views.order_invoice_view, name='order_invoice'),
]
