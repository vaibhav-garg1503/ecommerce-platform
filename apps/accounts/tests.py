from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from apps.accounts.models import Address

User = get_user_model()


class UserModelTests(TestCase):
    """Test custom User model behavior."""

    def test_create_user_success(self):
        user = User.objects.create_user(
            email='test@example.com',
            password='Password123!',
            first_name='John',
            last_name='Doe'
        )
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('Password123!'))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_email_verified)

    def test_create_superuser_success(self):
        admin = User.objects.create_superuser(
            email='admin@example.com',
            password='AdminPassword123!'
        )
        self.assertEqual(admin.email, 'admin@example.com')
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)


class AddressModelTests(TestCase):
    """Test Address model and default address switching behavior."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='addressuser@example.com',
            password='Password123!'
        )

    def test_create_address(self):
        addr = Address.objects.create(
            user=self.user,
            label='home',
            full_name='John Doe',
            phone='9876543210',
            address_line_1='123 Main St',
            city='Bangalore',
            state='Karnataka',
            pincode='560001',
            is_default=True
        )
        self.assertEqual(Address.objects.filter(user=self.user).count(), 1)
        self.assertTrue(addr.is_default)

    def test_default_address_switch(self):
        addr1 = Address.objects.create(
            user=self.user,
            label='home',
            full_name='John Doe',
            phone='9876543210',
            address_line_1='123 Main St',
            city='Bangalore',
            state='Karnataka',
            pincode='560001',
            is_default=True
        )
        addr2 = Address.objects.create(
            user=self.user,
            label='work',
            full_name='John Doe',
            phone='9876543210',
            address_line_1='456 Tech Park',
            city='Bangalore',
            state='Karnataka',
            pincode='560100',
            is_default=True
        )
        addr1.refresh_from_db()
        self.assertFalse(addr1.is_default)
        self.assertTrue(addr2.is_default)


class AuthViewsTests(TestCase):
    """Test login, logout, registration, and email verification views."""

    def setUp(self):
        self.client = Client()
        self.user_password = 'Password123!'
        self.user = User.objects.create_user(
            email='authuser@example.com',
            password=self.user_password,
            first_name='Jane',
            last_name='Doe'
        )

    def test_login_success(self):
        response = self.client.post(reverse('accounts:login'), {
            'email': 'authuser@example.com',
            'password': self.user_password
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue('_auth_user_id' in self.client.session)

    def test_login_invalid_credentials(self):
        response = self.client.post(reverse('accounts:login'), {
            'email': 'authuser@example.com',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse('_auth_user_id' in self.client.session)

    def test_registration_success(self):
        response = self.client.post(reverse('accounts:register'), {
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'phone': '9876543210',
            'password': 'NewPassword123!',
            'confirm_password': 'NewPassword123!'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(email='newuser@example.com').exists())

    def test_email_verification(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        response = self.client.get(reverse('accounts:verify_email', kwargs={'uidb64': uid, 'token': token}))
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_email_verified)

    def test_logout(self):
        self.client.login(email='authuser@example.com', password=self.user_password)
        response = self.client.get(reverse('accounts:logout'))
        self.assertEqual(response.status_code, 302)
        self.assertFalse('_auth_user_id' in self.client.session)
