from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from apps.orders.models import Order
from apps.orders.tasks import send_order_status_email

@receiver(pre_save, sender=Order)
def track_previous_status(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = Order.objects.get(pk=instance.pk)
            instance._previous_status = old_instance.status
        except Order.DoesNotExist:
            instance._previous_status = None
    else:
        instance._previous_status = None

@receiver(post_save, sender=Order)
def trigger_status_email(sender, instance, created, **kwargs):
    if not created and hasattr(instance, '_previous_status'):
        if instance.status != instance._previous_status:
            if instance.status in ['confirmed', 'shipped', 'delivered']:
                send_order_status_email.delay(instance.id)
