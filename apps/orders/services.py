from decimal import Decimal
from django.db import transaction
from apps.orders.models import Order, OrderItem, Coupon
from django.utils import timezone

class OrderService:
    @staticmethod
    @transaction.atomic
    def create_from_cart(cart, user, address, coupon_code=''):
        """Create an Order from a Cart, deducting stock and clearing the cart."""
        items = cart.items.select_related('variant').all()
        if not items.exists():
            raise ValueError("Cart is empty.")
            
        subtotal = cart.subtotal
        shipping_cost = Decimal('0.00') if subtotal >= Decimal('999.00') else Decimal('99.00')
        
        discount_amount = Decimal('0.00')
        if coupon_code:
            try:
                coupon = Coupon.objects.get(code=coupon_code)
                if coupon.is_valid(subtotal):
                    discount_amount = Decimal(str(coupon.apply(subtotal)))
                    coupon.uses_count += 1
                    coupon.save(update_fields=['uses_count'])
            except Coupon.DoesNotExist:
                pass
                
        total = subtotal + shipping_cost - discount_amount
        
        order = Order.objects.create(
            user=user,
            shipping_name=address.full_name,
            shipping_phone=address.phone,
            shipping_address_line_1=address.address_line_1,
            shipping_address_line_2=address.address_line_2,
            shipping_city=address.city,
            shipping_state=address.state,
            shipping_pincode=address.pincode,
            shipping_country=address.country,
            subtotal=subtotal,
            shipping_cost=shipping_cost,
            discount_amount=discount_amount,
            total=total,
            coupon_code=coupon_code,
            status='pending'
        )
        
        order_items = []
        for item in items:
            # Deduct stock
            if item.variant.stock_qty < item.quantity:
                raise ValueError(f"Not enough stock for {item.variant}.")
            item.variant.stock_qty -= item.quantity
            item.variant.save(update_fields=['stock_qty'])
            
            product_name = item.variant.product.name
            variant_info = ""
            parts = []
            if item.variant.size: parts.append(item.variant.size)
            if item.variant.color: parts.append(item.variant.color)
            if parts: variant_info = " / ".join(parts)
                
            order_items.append(OrderItem(
                order=order,
                variant=item.variant,
                product_name=product_name,
                variant_info=variant_info,
                quantity=item.quantity,
                price_at_purchase=item.variant.price
            ))
            
        OrderItem.objects.bulk_create(order_items)
        
        # Delete cart
        cart.delete()
        
        return order
    
    @staticmethod
    @transaction.atomic
    def cancel_order(order):
        """Cancel order and restore stock."""
        if order.status == 'cancelled':
            return
            
        order.status = 'cancelled'
        order.save(update_fields=['status', 'updated_at'])
        
        # Restore stock_qty for each item
        for item in order.items.select_related('variant').all():
            item.variant.stock_qty += item.quantity
            item.variant.save(update_fields=['stock_qty'])
