import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
from apps.orders.models import Order
from apps.orders.services import OrderService
from apps.payments.models import Payment
from apps.payments.services import PaymentService


@login_required
def payment_page_view(request, order_number):
    """GET shows Razorpay checkout or COD confirmation."""
    order = get_object_or_404(Order, order_number=order_number, user=request.user)

    if order.status != 'pending':
        return redirect('orders:order_detail', order_number=order.order_number)

    gateway = request.GET.get('gateway', 'razorpay')

    if gateway == 'cod':
        return render(request, 'payments/cod_confirm.html', {'order': order})

    # Razorpay flow
    rz_order = PaymentService.create_razorpay_order(order)
    context = {
        'order': order,
        'razorpay_order_id': rz_order['id'],
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
        'amount': rz_order['amount'],
    }
    return render(request, 'orders/order_confirm.html', context)


@login_required
@require_POST
def payment_callback_view(request):
    """POST endpoint called after Razorpay payment completes."""
    razorpay_payment_id = request.POST.get('razorpay_payment_id')
    razorpay_order_id = request.POST.get('razorpay_order_id')
    razorpay_signature = request.POST.get('razorpay_signature')
    order_number = request.POST.get('order_number')

    order = get_object_or_404(Order, order_number=order_number, user=request.user)

    is_valid = PaymentService.verify_signature(razorpay_order_id, razorpay_payment_id, razorpay_signature)

    if is_valid:
        order.status = 'confirmed'
        order.save(update_fields=['status', 'updated_at'])
        Payment.objects.create(
            order=order,
            gateway='razorpay',
            transaction_id=razorpay_payment_id,
            amount=order.total,
            status='captured',
            gateway_response={'razorpay_order_id': razorpay_order_id}
        )
        return render(request, 'payments/payment_success.html', {'order': order})
    else:
        OrderService.cancel_order(order)
        return render(request, 'payments/payment_failed.html', {'order': order})


@csrf_exempt
@require_POST
def payment_webhook_view(request):
    """POST webhook from Razorpay as second source of truth."""
    return HttpResponse(status=200)


@login_required
@require_POST
def cod_place_order_view(request, order_number):
    """POST for Cash on Delivery orders."""
    order = get_object_or_404(Order, order_number=order_number, user=request.user)

    if order.status != 'pending':
        return redirect('orders:order_detail', order_number=order.order_number)

    order.status = 'confirmed'
    order.save(update_fields=['status', 'updated_at'])
    Payment.objects.create(
        order=order,
        gateway='cod',
        amount=order.total,
        status='pending'
    )
    return render(request, 'payments/payment_success.html', {'order': order})
