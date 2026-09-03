from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from apps.cart.services import CartService

@receiver(user_logged_in)
def merge_guest_cart_on_login(sender, request, user, **kwargs):
    session_key = request.session.session_key
    if session_key:
        CartService.merge_carts(session_key, user)
