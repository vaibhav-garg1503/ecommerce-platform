from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from apps.cart.services import CartService
from apps.cart.models import CartItem

def cart_detail_view(request):
    cart = CartService.get_or_create_cart(request)
    items = cart.items.select_related('variant', 'variant__product')
    
    subtotal = cart.subtotal
    shipping_estimate = 0 if subtotal >= 999 else 99
    if subtotal == 0:
        shipping_estimate = 0
    grand_total = subtotal + shipping_estimate
    
    context = {
        'cart': cart,
        'items': items,
        'subtotal': subtotal,
        'shipping_estimate': shipping_estimate,
        'grand_total': grand_total,
        'free_shipping_threshold': 999,
        'amount_to_free_shipping': max(0, 999 - subtotal),
    }
    return render(request, 'cart/cart_detail.html', context)

def cart_add_view(request):
    if request.method == 'POST':
        variant_id = request.POST.get('variant_id')
        quantity = int(request.POST.get('quantity', 1))
        
        cart = CartService.get_or_create_cart(request)
        
        try:
            CartService.add_to_cart(cart, variant_id, quantity)
            messages.success(request, "Item added to cart.")
        except ValueError as e:
            messages.error(request, str(e))
            
        if request.headers.get('HX-Request'):
            response = render(request, 'cart/partials/cart_badge.html', {'cart': cart})
            response['HX-Trigger'] = 'cartUpdated'
            return response
            
        return redirect('cart:cart_detail')
    return redirect('catalog:product_list')

def cart_update_view(request, item_id):
    if request.method == 'POST':
        cart = CartService.get_or_create_cart(request)
        
        action = request.POST.get('action')
        quantity_str = request.POST.get('quantity')
        
        try:
            item = CartItem.objects.get(cart=cart, id=item_id)
            current_qty = item.quantity
            
            if action == 'inc':
                new_qty = current_qty + 1
            elif action == 'dec':
                new_qty = current_qty - 1
            elif quantity_str is not None:
                new_qty = int(quantity_str)
            else:
                new_qty = current_qty
                
            updated_item = CartService.update_quantity(cart, item_id, new_qty)
            
            if request.headers.get('HX-Request'):
                if updated_item:
                    context = {
                        'item': updated_item,
                        'cart': cart,
                    }
                    response = render(request, 'cart/partials/cart_item_row.html', context)
                else:
                    response = HttpResponse("")
                response['HX-Trigger'] = 'cartUpdated'
                return response
        except ValueError as e:
            messages.error(request, str(e))
            if request.headers.get('HX-Request'):
                response = render(request, 'cart/partials/cart_item_row.html', {'item': item, 'cart': cart, 'error': str(e)})
                return response
        except CartItem.DoesNotExist:
            pass
            
    return redirect('cart:cart_detail')

def cart_remove_view(request, item_id):
    if request.method == 'POST':
        cart = CartService.get_or_create_cart(request)
        CartService.remove_from_cart(cart, item_id)
        messages.success(request, "Item removed from cart.")
    return redirect('cart:cart_detail')

def cart_badge_view(request):
    cart = CartService.get_or_create_cart(request)
    return render(request, 'cart/partials/cart_badge.html', {'cart': cart})
