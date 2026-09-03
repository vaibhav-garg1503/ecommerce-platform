from django.contrib import admin
from apps.payments.models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'order', 'gateway', 'amount', 'status', 'created_at')
    list_filter = ('gateway', 'status')
