import io
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.catalog.models import Category, Product, ProductVariant
from apps.catalog.services import BulkProductImporter

User = get_user_model()


class CatalogModelTests(TestCase):
    """Test Category, Product, and ProductVariant model logic."""

    def setUp(self):
        self.category = Category.objects.create(name='Clothing')
        self.product = Product.objects.create(
            category=self.category,
            name='Cotton T-Shirt',
            brand='Nike',
            description='Comfortable cotton shirt'
        )
        self.variant_m = ProductVariant.objects.create(
            product=self.product,
            sku='TSHIRT-RED-M',
            size='M',
            color='Red',
            price=Decimal('29.99'),
            compare_at_price=Decimal('39.99'),
            stock_qty=10,
            low_stock_threshold=3
        )
        self.variant_l = ProductVariant.objects.create(
            product=self.product,
            sku='TSHIRT-RED-L',
            size='L',
            color='Red',
            price=Decimal('19.99'),
            stock_qty=2,
            low_stock_threshold=5
        )

    def test_category_slug_auto_generation(self):
        self.assertEqual(self.category.slug, 'clothing')

    def test_product_properties(self):
        self.assertEqual(self.product.min_price, Decimal('19.99'))
        self.assertTrue(self.product.in_stock)

    def test_low_stock_detection(self):
        self.assertFalse(self.variant_m.is_low_stock)  # stock 10 > threshold 3
        self.assertTrue(self.variant_l.is_low_stock)   # stock 2 <= threshold 5


class BulkProductImporterTests(TestCase):
    """Test CSV bulk import service."""

    def test_valid_csv_import(self):
        csv_data = (
            "category,product_name,brand,description,sku,size,color,price,compare_at_price,stock_qty,low_stock_threshold\n"
            "Footwear,Air Max,Nike,Running shoes,NIKE-AM-9,9,Black,120.00,150.00,15,5\n"
            "Footwear,Air Max,Nike,Running shoes,NIKE-AM-10,10,Black,120.00,150.00,3,5\n"
        )
        file_obj = io.StringIO(csv_data)
        importer = BulkProductImporter()
        result = importer.process_csv(file_obj)

        self.assertEqual(result['created_products'], 1)
        self.assertEqual(result['created_variants'], 2)
        self.assertEqual(result['total_variants'], 2)
        self.assertEqual(len(result['errors']), 0)
        self.assertTrue(Category.objects.filter(name='Footwear').exists())
        self.assertTrue(ProductVariant.objects.filter(sku='NIKE-AM-9').exists())

    def test_invalid_csv_row_handling(self):
        csv_data = (
            "category,product_name,brand,description,sku,size,color,price,compare_at_price,stock_qty,low_stock_threshold\n"
            ",Missing Category,Nike,Desc,INVALID-SKU,M,Red,50.00,,10,2\n"
        )
        file_obj = io.StringIO(csv_data)
        importer = BulkProductImporter()
        result = importer.process_csv(file_obj)

        self.assertEqual(len(result['errors']), 1)
        self.assertIn("Category name is required", result['errors'][0])


class CatalogAdminViewsTests(TestCase):
    """Test staff access to bulk import and low-stock admin views."""

    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_superuser(
            email='staff@example.com',
            password='Password123!'
        )
        self.normal_user = User.objects.create_user(
            email='normal@example.com',
            password='Password123!'
        )

    def test_sample_csv_download_access(self):
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse('catalog:admin_sample_csv'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')

    def test_non_staff_access_denied(self):
        self.client.force_login(self.normal_user)
        response = self.client.get(reverse('catalog:admin_bulk_import'))
        self.assertEqual(response.status_code, 302)  # Redirects to admin login


class StorefrontViewsTests(TestCase):
    """Test customer-facing Storefront views (Phase 3)."""

    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name='Electronics', slug='electronics')
        self.product = Product.objects.create(
            category=self.category,
            name='Wireless Headphones',
            slug='wireless-headphones',
            brand='Sony',
            description='Noise cancelling headphones',
            is_active=True,
            is_featured=True
        )
        self.variant = ProductVariant.objects.create(
            product=self.product,
            sku='SONY-WH-1000',
            size='One Size',
            color='Black',
            price=Decimal('299.99'),
            stock_qty=15,
            is_active=True
        )

    def test_homepage_view(self):
        response = self.client.get(reverse('catalog:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Wireless Headphones')

    def test_product_list_view(self):
        response = self.client.get(reverse('catalog:product_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Wireless Headphones')

    def test_product_list_filtering(self):
        response = self.client.get(reverse('catalog:product_list'), {'q': 'Sony'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['page_obj']), 1)

        response_empty = self.client.get(reverse('catalog:product_list'), {'q': 'NonExistentProduct'})
        self.assertEqual(response_empty.status_code, 200)
        self.assertEqual(len(response_empty.context['page_obj']), 0)

    def test_product_detail_view(self):
        response = self.client.get(reverse('catalog:product_detail', kwargs={'slug': self.product.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Wireless Headphones')
        self.assertContains(response, '299.99')

    def test_search_autocomplete(self):
        response = self.client.get(reverse('catalog:search_autocomplete'), {'q': 'Wireless'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Wireless Headphones')

    def test_variant_info_api(self):
        response = self.client.get(reverse('catalog:variant_info', kwargs={'variant_id': self.variant.id}))
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertEqual(json_data['price'], '299.99')
        self.assertTrue(json_data['in_stock'])

    def test_sitemap_and_robots(self):
        response_sitemap = self.client.get(reverse('catalog:sitemap'))
        self.assertEqual(response_sitemap.status_code, 200)
        self.assertIn('xml', response_sitemap['Content-Type'])

        response_robots = self.client.get(reverse('catalog:robots'))
        self.assertEqual(response_robots.status_code, 200)
        self.assertContains(response_robots, 'User-agent')
