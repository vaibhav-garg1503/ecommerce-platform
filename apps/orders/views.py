import json
from decimal import Decimal
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from apps.cart.models import Cart
from apps.accounts.models import Address
from apps.orders.models import Order, Coupon
from apps.orders.services import OrderService

@login_required
def order_invoice_view(request, order_number):
    """Renders printable invoice."""
    order = get_object_or_404(Order, order_number=order_number)
    
    if order.user != request.user and not request.user.is_staff:
        raise PermissionDenied
        
    context = {'order': order}
    return render(request, 'orders/invoice.html', context)

@login_required
def checkout_view(request):
    """GET shows checkout form (address selection + coupon input). POST validates and redirects to payment."""
    cart = Cart.objects.filter(user=request.user).first()
    if not cart or not cart.items.exists():
        return redirect('cart:cart_detail') # assuming a cart detail view exists

    if request.method == 'POST':
        address_id = request.POST.get('address_id')
        coupon_code = request.POST.get('coupon_code', '')
        
        # If user submits a new address
        if request.POST.get('new_address') == 'true':
            address = Address.objects.create(
                user=request.user,
                full_name=request.POST.get('full_name'),
                phone=request.POST.get('phone'),
                address_line_1=request.POST.get('address_line_1'),
                address_line_2=request.POST.get('address_line_2', ''),
                city=request.POST.get('city'),
                state=request.POST.get('state'),
                pincode=request.POST.get('pincode'),
                country=request.POST.get('country', 'India')
            )
        else:
            address = get_object_or_404(Address, id=address_id, user=request.user)

        try:
            order = OrderService.create_from_cart(cart, request.user, address, coupon_code)
            payment_method = request.POST.get('payment_method', 'razorpay')
            from django.urls import reverse
            url = reverse('payments:payment_page', args=[order.order_number])
            return redirect(f"{url}?gateway={payment_method}")
        except ValueError as e:
            # Handle out of stock, etc
            pass

    addresses = Address.objects.filter(user=request.user)
    
    subtotal = cart.subtotal
    shipping_cost = Decimal('0.00') if subtotal >= Decimal('999.00') else Decimal('99.00')
    total = subtotal + shipping_cost

    context = {
        'cart': cart,
        'addresses': addresses,
        'subtotal': subtotal,
        'shipping_cost': shipping_cost,
        'total': total,
    }
    return render(request, 'orders/checkout.html', context)


@login_required
def order_confirm_view(request, order_number):
    """Shows order confirmation summary before payment — creates Razorpay order."""
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    if order.status != 'pending':
        return redirect('orders:order_detail', order_number=order.order_number)

    from apps.payments.services import PaymentService
    from django.conf import settings
    rz_order = PaymentService.create_razorpay_order(order)

    context = {
        'order': order,
        'razorpay_order_id': rz_order['id'],
        'razorpay_key_id': getattr(settings, 'RAZORPAY_KEY_ID', ''),
        'amount': rz_order['amount'],
    }
    return render(request, 'orders/order_confirm.html', context)


@login_required
def order_list_view(request):
    """Lists user's orders."""
    orders = Order.objects.filter(user=request.user)
    context = {'orders': orders}
    return render(request, 'orders/order_list.html', context)


@login_required
def order_detail_view(request, order_number):
    """Shows full order detail and status timeline."""
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    context = {'order': order}
    return render(request, 'orders/order_detail.html', context)


@login_required
@require_POST
def apply_coupon_view(request):
    """AJAX POST, validates coupon, returns JSON discount info."""
    try:
        data = json.loads(request.body)
        coupon_code = data.get('coupon_code')
        cart_subtotal = Decimal(str(data.get('subtotal', 0)))
        
        try:
            coupon = Coupon.objects.get(code=coupon_code)
            if coupon.is_valid(cart_subtotal):
                discount = coupon.apply(cart_subtotal)
                return JsonResponse({
                    'success': True,
                    'discount_amount': float(discount),
                    'message': 'Coupon applied successfully!'
                })
            else:
                return JsonResponse({'success': False, 'message': 'Coupon is invalid or expired.'})
        except Coupon.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Coupon not found.'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})
