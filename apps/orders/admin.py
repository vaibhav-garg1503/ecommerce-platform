from django.contrib import admin
from apps.orders.models import Order, OrderItem, Shipment
from apps.payments.models import Payment

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = [f.name for f in OrderItem._meta.fields]

    def has_add_permission(self, request, obj):
        return False

    def has_delete_permission(self, request, obj):
        return False

class ShipmentInline(admin.StackedInline):
    model = Shipment
    extra = 0

class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = [f.name for f in Payment._meta.fields]

    def has_add_permission(self, request, obj):
        return False

    def has_delete_permission(self, request, obj):
        return False

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'user', 'status', 'total', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('order_number', 'user__email', 'shipping_name')
    inlines = [OrderItemInline, ShipmentInline, PaymentInline]
    actions = ['mark_as_shipped']

    @admin.action(description='Mark selected orders as shipped')
    def mark_as_shipped(self, request, queryset):
        for order in queryset:
            order.status = 'shipped'
            order.save(update_fields=['status', 'updated_at'])
        self.message_user(request, 'Selected orders marked as shipped.')
