from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.catalog.models import Category, Product, ProductVariant
from apps.cart.models import Cart, CartItem
from apps.cart.services import CartService

User = get_user_model()


class CartServiceTests(TestCase):
    """Test CartService logic for guest carts, user carts, stock limits, and cart merging."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='cartuser@example.com',
            password='Password123!'
        )
        self.category = Category.objects.create(name='Gadgets')
        self.product = Product.objects.create(
            category=self.category,
            name='Smart Watch',
            brand='TechCorp'
        )
        self.variant_in_stock = ProductVariant.objects.create(
            product=self.product,
            sku='WATCH-BLK',
            color='Black',
            size='Standard',
            price=Decimal('150.00'),
            stock_qty=10
        )
        self.variant_low_stock = ProductVariant.objects.create(
            product=self.product,
            sku='WATCH-SLV',
            color='Silver',
            size='Standard',
            price=Decimal('180.00'),
            stock_qty=2
        )

    def test_add_to_guest_cart(self):
        session = self.client.session
        session.create()

        class DummyRequest:
            pass

        req = DummyRequest()
        req.user = type('AnonymousUser', (), {'is_authenticated': False})()
        req.session = session

        cart = CartService.get_or_create_cart(req)
        self.assertIsNotNone(cart.session_key)

        item = CartService.add_to_cart(cart, self.variant_in_stock.id, quantity=2)
        self.assertEqual(item.quantity, 2)
        self.assertEqual(cart.total_items, 2)
        self.assertEqual(cart.subtotal, Decimal('300.00'))

    def test_stock_limit_enforcement(self):
        cart = Cart.objects.create(user=self.user)
        with self.assertRaises(ValueError):
            CartService.add_to_cart(cart, self.variant_low_stock.id, quantity=5)

    def test_cart_update_quantity(self):
        cart = Cart.objects.create(user=self.user)
        item = CartService.add_to_cart(cart, self.variant_in_stock.id, quantity=1)

        updated_item = CartService.update_quantity(cart, item.id, quantity=4)
        self.assertEqual(updated_item.quantity, 4)
        self.assertEqual(cart.subtotal, Decimal('600.00'))

        # Setting quantity to 0 removes the item
        removed_item = CartService.update_quantity(cart, item.id, quantity=0)
        self.assertIsNone(removed_item)
        self.assertEqual(cart.total_items, 0)

    def test_cart_remove_item(self):
        cart = Cart.objects.create(user=self.user)
        item = CartService.add_to_cart(cart, self.variant_in_stock.id, quantity=2)

        CartService.remove_from_cart(cart, item.id)
        self.assertEqual(CartItem.objects.filter(cart=cart).count(), 0)

    def test_merge_guest_cart_on_login(self):
        guest_session_key = "guest_session_12345"
        guest_cart = Cart.objects.create(session_key=guest_session_key)
        CartItem.objects.create(cart=guest_cart, variant=self.variant_in_stock, quantity=3)

        CartService.merge_carts(guest_session_key, self.user)

        user_cart = Cart.objects.get(user=self.user)
        self.assertEqual(user_cart.total_items, 3)
        self.assertFalse(Cart.objects.filter(id=guest_cart.id).exists())


class CartViewsTests(TestCase):
    """Test Cart endpoints and user flows."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='viewuser@example.com',
            password='Password123!'
        )
        self.category = Category.objects.create(name='Apparel')
        self.product = Product.objects.create(category=self.category, name='Jacket')
        self.variant = ProductVariant.objects.create(
            product=self.product,
            sku='JKT-BLK-L',
            color='Black',
            size='L',
            price=Decimal('89.99'),
            stock_qty=5
        )

    def test_cart_detail_view(self):
        response = self.client.get(reverse('cart:cart_detail'))
        self.assertEqual(response.status_code, 200)

    def test_cart_add_post(self):
        response = self.client.post(reverse('cart:cart_add'), {
            'variant_id': self.variant.id,
            'quantity': 2
        })
        self.assertEqual(response.status_code, 302)
        cart = Cart.objects.filter(items__variant=self.variant).first()
        self.assertIsNotNone(cart)
        self.assertEqual(cart.total_items, 2)

    def test_cart_badge_view(self):
        response = self.client.get(reverse('cart:cart_badge'))
        self.assertEqual(response.status_code, 200)
