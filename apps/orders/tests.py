from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from apps.catalog.models import Category, Product, ProductVariant
from apps.cart.models import Cart, CartItem
from apps.orders.models import Order, OrderItem, Coupon
from apps.orders.services import OrderService
from apps.orders.tasks import cancel_unpaid_orders

User = get_user_model()


def make_user(email='test@example.com', password='Password123!'):
    return User.objects.create_user(email=email, password=password)


def make_variant(name='Product', sku='SKU-001', price='99.99', stock=10):
    cat = Category.objects.get_or_create(name='Test')[0]
    # Each variant gets its own product to avoid unique_product_variant constraint
    prod = Product.objects.get_or_create(
        name=f'{name}-{sku}', category=cat, defaults={'brand': 'Brand'}
    )[0]
    return ProductVariant.objects.create(
        product=prod, sku=sku, size='M', color='Red',
        price=Decimal(price), stock_qty=stock
    )


def make_address(user):
    from apps.accounts.models import Address
    return Address.objects.create(
        user=user,
        full_name='Test User',
        phone='9876543210',
        address_line_1='123 Main St',
        city='Mumbai',
        state='Maharashtra',
        pincode='400001',
        country='India',
    )


class OrderServiceTests(TestCase):
    """Test OrderService.create_from_cart and cancel_order."""

    def setUp(self):
        self.user = make_user()
        self.variant = make_variant(sku='SKU-OS-1', price='500.00', stock=10)
        self.address = make_address(self.user)

    def test_create_order_from_cart(self):
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, variant=self.variant, quantity=2)

        order = OrderService.create_from_cart(cart, self.user, self.address)

        self.assertEqual(order.status, 'pending')
        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.subtotal, Decimal('1000.00'))  # 2 × 500
        self.assertEqual(order.shipping_cost, Decimal('0.00'))  # free above 999
        self.assertEqual(order.total, Decimal('1000.00'))
        self.assertTrue(order.order_number.startswith('ORD-'))
        # Stock should be deducted
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.stock_qty, 8)
        # Cart should be deleted
        self.assertFalse(Cart.objects.filter(user=self.user).exists())

    def test_shipping_cost_below_999(self):
        variant_cheap = make_variant(sku='SKU-OS-2', price='200.00', stock=5)
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, variant=variant_cheap, quantity=1)

        order = OrderService.create_from_cart(cart, self.user, self.address)

        self.assertEqual(order.shipping_cost, Decimal('99.00'))
        self.assertEqual(order.total, Decimal('299.00'))

    def test_empty_cart_raises_error(self):
        cart = Cart.objects.create(user=self.user)
        with self.assertRaises(ValueError):
            OrderService.create_from_cart(cart, self.user, self.address)

    def test_insufficient_stock_raises_error(self):
        variant_low = make_variant(sku='SKU-OS-3', price='100.00', stock=1)
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, variant=variant_low, quantity=5)

        with self.assertRaises(ValueError):
            OrderService.create_from_cart(cart, self.user, self.address)

    def test_cancel_order_restores_stock(self):
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, variant=self.variant, quantity=3)
        order = OrderService.create_from_cart(cart, self.user, self.address)

        self.variant.refresh_from_db()
        stock_after_order = self.variant.stock_qty  # 10 - 3 = 7

        OrderService.cancel_order(order)

        self.variant.refresh_from_db()
        self.assertEqual(self.variant.stock_qty, stock_after_order + 3)  # restored
        order.refresh_from_db()
        self.assertEqual(order.status, 'cancelled')


class CouponTests(TestCase):
    """Test Coupon model validation and application."""

    def setUp(self):
        self.coupon = Coupon.objects.create(
            code='SAVE20',
            discount_percent=20,
            min_order_value=Decimal('500.00'),
            max_uses=100,
            valid_from=timezone.now() - timedelta(days=1),
            valid_to=timezone.now() + timedelta(days=30),
            is_active=True,
        )

    def test_valid_coupon(self):
        self.assertTrue(self.coupon.is_valid(Decimal('600.00')))

    def test_coupon_below_min_order(self):
        self.assertFalse(self.coupon.is_valid(Decimal('400.00')))

    def test_expired_coupon(self):
        self.coupon.valid_to = timezone.now() - timedelta(days=1)
        self.coupon.save()
        self.assertFalse(self.coupon.is_valid(Decimal('600.00')))

    def test_coupon_discount_applied(self):
        # 20% off 600 = 120
        discount = self.coupon.apply(Decimal('600.00'))
        self.assertEqual(Decimal(str(discount)), Decimal('120.00'))

    def test_flat_coupon(self):
        flat_coupon = Coupon.objects.create(
            code='FLAT50',
            discount_flat=Decimal('50.00'),
            min_order_value=Decimal('300.00'),
            max_uses=10,
            valid_from=timezone.now() - timedelta(days=1),
            valid_to=timezone.now() + timedelta(days=10),
        )
        self.assertEqual(Decimal(str(flat_coupon.apply(Decimal('400.00')))), Decimal('50.00'))


class OrderWithCouponTests(TestCase):
    """Test coupon discount is applied during order creation."""

    def setUp(self):
        self.user = make_user(email='couponuser@example.com')
        self.variant = make_variant(sku='SKU-CP-1', price='600.00', stock=5)
        self.address = make_address(self.user)
        self.coupon = Coupon.objects.create(
            code='TEST10',
            discount_percent=10,
            min_order_value=Decimal('500.00'),
            max_uses=50,
            valid_from=timezone.now() - timedelta(days=1),
            valid_to=timezone.now() + timedelta(days=30),
        )

    def test_order_with_valid_coupon(self):
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, variant=self.variant, quantity=1)

        order = OrderService.create_from_cart(cart, self.user, self.address, coupon_code='TEST10')

        self.assertEqual(order.discount_amount, Decimal('60.00'))  # 10% of 600
        self.assertEqual(order.shipping_cost, Decimal('99.00'))    # below 999 threshold
        self.assertEqual(order.total, Decimal('639.00'))   # 600 + 99 shipping - 60 discount

        self.coupon.refresh_from_db()
        self.assertEqual(self.coupon.uses_count, 1)


class AutoCancelTaskTests(TestCase):
    """Test Celery task cancels stale pending orders."""

    def test_cancel_unpaid_orders_task(self):
        user = make_user(email='taskuser@example.com')
        variant = make_variant(sku='SKU-TASK-1', price='200.00', stock=10)
        address = make_address(user)

        cart = Cart.objects.create(user=user)
        CartItem.objects.create(cart=cart, variant=variant, quantity=2)
        order = OrderService.create_from_cart(cart, user, address)

        # Simulate order being 25 hours old
        Order.objects.filter(pk=order.pk).update(
            created_at=timezone.now() - timedelta(hours=25)
        )

        result = cancel_unpaid_orders()

        order.refresh_from_db()
        self.assertEqual(order.status, 'cancelled')
        self.assertIn('Cancelled 1', result)


class CheckoutViewTests(TestCase):
    """Test checkout, order list, and order detail views."""

    def setUp(self):
        self.client = Client()
        self.user = make_user(email='checkoutview@example.com')
        self.client.force_login(self.user)
        self.variant = make_variant(sku='SKU-CV-1', price='300.00', stock=5)
        self.address = make_address(self.user)

    def test_checkout_redirects_when_cart_empty(self):
        response = self.client.get(reverse('orders:checkout'))
        self.assertEqual(response.status_code, 302)  # redirect back

    def test_order_list_view(self):
        response = self.client.get(reverse('orders:order_list'))
        self.assertEqual(response.status_code, 200)

    def test_order_detail_view(self):
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, variant=self.variant, quantity=1)
        order = OrderService.create_from_cart(cart, self.user, self.address)

        response = self.client.get(reverse('orders:order_detail', kwargs={'order_number': order.order_number}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, order.order_number)

    def test_order_invoice_view_access(self):
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, variant=self.variant, quantity=1)
        order = OrderService.create_from_cart(cart, self.user, self.address)

        # User who owns order
        response = self.client.get(reverse('orders:order_invoice', kwargs={'order_number': order.order_number}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'INVOICE')
        self.assertContains(response, order.order_number)

        # Other user
        other_user = make_user(email='otheruser@example.com')
        self.client.force_login(other_user)
        response = self.client.get(reverse('orders:order_invoice', kwargs={'order_number': order.order_number}))
        self.assertEqual(response.status_code, 403)

        # Staff user
        staff_user = make_user(email='staffuser@example.com')
        staff_user.is_staff = True
        staff_user.save()
        self.client.force_login(staff_user)
        response = self.client.get(reverse('orders:order_invoice', kwargs={'order_number': order.order_number}))
        self.assertEqual(response.status_code, 200)

class OrderEmailTests(TestCase):
    def setUp(self):
        self.user = make_user(email='emailtest@example.com')
        self.variant = make_variant(sku='SKU-EM-1', price='100.00', stock=5)
        self.address = make_address(self.user)

    def test_order_status_email(self):
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, variant=self.variant, quantity=1)
        
        from unittest.mock import patch
        
        # Patch the Celery delay method on the task so we don't try to connect to the broker during tests
        with patch('apps.orders.tasks.send_order_status_email.delay') as mock_delay:
            order = OrderService.create_from_cart(cart, self.user, self.address)

            # Change status to trigger email
            order.status = 'confirmed'
            order.save()
            
            # Ensure the delay method was called once when the status changed
            self.assertEqual(mock_delay.call_count, 1)

        from django.core import mail
        mail.outbox = []

        # Test the task directly to ensure it sends the email properly
        from apps.orders.tasks import send_order_status_email
        send_order_status_email(order.id)
        
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Status Update', mail.outbox[0].subject)
