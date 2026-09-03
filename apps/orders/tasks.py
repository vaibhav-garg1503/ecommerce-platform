from celery import shared_task
from django.utils import timezone
from datetime import timedelta

@shared_task
def cancel_unpaid_orders():
    """Cancel orders that remain 'pending' payment for more than 24 hours and restore stock."""
    from apps.orders.models import Order
    from apps.orders.services import OrderService
    
    cutoff = timezone.now() - timedelta(hours=24)
    pending_orders = Order.objects.filter(status='pending', created_at__lt=cutoff)
    
    count = 0
    for order in pending_orders:
        OrderService.cancel_order(order)
        count += 1
        
    return f'Cancelled {count} unpaid orders.'

@shared_task
def send_order_status_email(order_id):
    from apps.orders.models import Order
    from django.core.mail import send_mail
    from django.conf import settings
    try:
        order = Order.objects.get(id=order_id)
        subject = f"Order {order.order_number} Status Update"
        message = f"Hello,\n\nYour order {order.order_number} is now {order.get_status_display()}.\n\nThank you for shopping with us!"
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [order.user.email],
            fail_silently=False,
        )
        return f"Sent status email for order {order_id}"
    except Order.DoesNotExist:
        return f"Order {order_id} not found"
