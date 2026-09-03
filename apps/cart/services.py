from django.core.exceptions import ObjectDoesNotExist
from apps.cart.models import Cart, CartItem
from apps.catalog.models import ProductVariant

class CartService:
    @staticmethod
    def get_or_create_cart(request):
        if request.user.is_authenticated:
            cart, _ = Cart.objects.get_or_create(user=request.user)
            return cart
        else:
            if not request.session.session_key:
                request.session.create()
            session_key = request.session.session_key
            cart, _ = Cart.objects.get_or_create(session_key=session_key, user__isnull=True)
            return cart

    @staticmethod
    def add_to_cart(cart, variant_id, quantity=1):
        variant = ProductVariant.objects.get(id=variant_id)
        
        try:
            item = CartItem.objects.get(cart=cart, variant=variant)
            new_quantity = item.quantity + int(quantity)
        except CartItem.DoesNotExist:
            item = CartItem(cart=cart, variant=variant, quantity=0)
            new_quantity = int(quantity)
            
        if new_quantity > variant.stock_qty:
            raise ValueError(f"Only {variant.stock_qty} units available in stock.")
            
        item.quantity = new_quantity
        item.save()
        return item

    @staticmethod
    def update_quantity(cart, item_id, quantity):
        quantity = int(quantity)
        try:
            item = CartItem.objects.get(cart=cart, id=item_id)
        except CartItem.DoesNotExist:
            return None

        if quantity <= 0:
            item.delete()
            return None
            
        if quantity > item.variant.stock_qty:
            raise ValueError(f"Only {item.variant.stock_qty} units available in stock.")
            
        item.quantity = quantity
        item.save()
        return item

    @staticmethod
    def remove_from_cart(cart, item_id):
        CartItem.objects.filter(cart=cart, id=item_id).delete()

    @staticmethod
    def merge_carts(guest_session_key, user):
        try:
            guest_cart = Cart.objects.get(session_key=guest_session_key, user__isnull=True)
            if not guest_cart.items.exists():
                guest_cart.delete()
                return

            user_cart, _ = Cart.objects.get_or_create(user=user)
            
            for guest_item in guest_cart.items.all():
                try:
                    user_item = CartItem.objects.get(cart=user_cart, variant=guest_item.variant)
                    new_qty = user_item.quantity + guest_item.quantity
                    user_item.quantity = min(new_qty, guest_item.variant.stock_qty)
                    user_item.save()
                except CartItem.DoesNotExist:
                    # Just re-link to the user's cart
                    guest_item.cart = user_cart
                    guest_item.quantity = min(guest_item.quantity, guest_item.variant.stock_qty)
                    guest_item.save()
            
            guest_cart.delete()
        except Cart.DoesNotExist:
            pass
