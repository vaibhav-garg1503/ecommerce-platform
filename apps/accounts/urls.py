from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('verify-email/<str:uidb64>/<str:token>/', views.verify_email_view, name='verify_email'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('addresses/', views.address_list_view, name='addresses'),
    path('addresses/list/', views.address_list_view, name='address_list'),
    path('addresses/add/', views.address_create_view, name='address_create'),
    path('addresses/<int:pk>/edit/', views.address_update_view, name='address_update'),
    path('addresses/<int:pk>/delete/', views.address_delete_view, name='address_delete'),
    path('addresses/<int:pk>/set-default/', views.address_set_default_view, name='address_set_default'),
    path('password-reset/', views.password_reset_request_view, name='password_reset'),
    path('password-reset/confirm/<str:uidb64>/<str:token>/', views.password_reset_confirm_view, name='password_reset_confirm'),
    path('resend_verification/', views.resend_verification, name='resend_verification'),
]
