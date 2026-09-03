from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from apps.catalog.models import Category, Product, ProductVariant
from apps.cms.models import Banner


class Command(BaseCommand):
    help = "Seed catalog with sample categories, products, variants, and banners for testing."

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Seeding catalog data..."))

        # Banners
        Banner.objects.get_or_create(
            title="Summer Collection 2026",
            defaults={
                'subtitle': 'Up to 40% Off Premium Apparel & Footwear',
                'link': '/shop/',
                'sort_order': 1,
                'is_active': True
            }
        )
        Banner.objects.get_or_create(
            title="Tech & Audio Deals",
            defaults={
                'subtitle': 'Explore Premium Noise-Cancelling Headphones & Gear',
                'link': '/shop/',
                'sort_order': 2,
                'is_active': True
            }
        )

        # Categories
        electronics, _ = Category.objects.get_or_create(name="Electronics", defaults={'sort_order': 1, 'is_active': True})
        apparel, _ = Category.objects.get_or_create(name="Apparel", defaults={'sort_order': 2, 'is_active': True})
        footwear, _ = Category.objects.get_or_create(name="Footwear", defaults={'sort_order': 3, 'is_active': True})

        # Sample Products
        # 1. Headphones
        hp, _ = Product.objects.get_or_create(
            name="Wireless Pro Headphones",
            category=electronics,
            defaults={
                'brand': 'AudioMax',
                'description': 'Premium active noise cancelling wireless over-ear headphones with 30-hour battery life and ultra-comfortable memory foam earcups.',
                'is_active': True,
                'is_featured': True,
                'meta_title': 'AudioMax Wireless Pro Headphones',
                'meta_description': 'Buy AudioMax Wireless Pro Headphones online at best price.'
            }
        )
        ProductVariant.objects.get_or_create(
            sku="HP-BLACK-ONESIZE",
            defaults={
                'product': hp,
                'color': 'Black',
                'size': 'One Size',
                'price': Decimal('199.99'),
                'compare_at_price': Decimal('249.99'),
                'stock_qty': 25,
                'low_stock_threshold': 5
            }
        )
        ProductVariant.objects.get_or_create(
            sku="HP-SILVER-ONESIZE",
            defaults={
                'product': hp,
                'color': 'Silver',
                'size': 'One Size',
                'price': Decimal('209.99'),
                'compare_at_price': Decimal('259.99'),
                'stock_qty': 4,
                'low_stock_threshold': 5
            }
        )

        # 2. T-Shirt
        ts, _ = Product.objects.get_or_create(
            name="Classic Organic Cotton T-Shirt",
            category=apparel,
            defaults={
                'brand': 'EcoWear',
                'description': '100% certified organic cotton crew neck t-shirt. Breathable, durable, and ethically manufactured.',
                'is_active': True,
                'is_featured': True
            }
        )
        for size in ['S', 'M', 'L', 'XL']:
            ProductVariant.objects.get_or_create(
                sku=f"TS-NAVY-{size}",
                defaults={
                    'product': ts,
                    'color': 'Navy',
                    'size': size,
                    'price': Decimal('29.99'),
                    'compare_at_price': Decimal('39.99'),
                    'stock_qty': 15,
                    'low_stock_threshold': 3
                }
            )

        # 3. Running Shoes
        rs, _ = Product.objects.get_or_create(
            name="Velocity Air Running Shoes",
            category=footwear,
            defaults={
                'brand': 'SpeedRun',
                'description': 'Lightweight road running shoes with responsive foam cushioning and breathable knit upper.',
                'is_active': True,
                'is_featured': True
            }
        )
        for size in ['8', '9', '10', '11']:
            ProductVariant.objects.get_or_create(
                sku=f"RS-RED-{size}",
                defaults={
                    'product': rs,
                    'color': 'Red',
                    'size': size,
                    'price': Decimal('119.99'),
                    'compare_at_price': Decimal('149.99'),
                    'stock_qty': 8 if size != '11' else 2,
                    'low_stock_threshold': 3
                }
            )

        self.stdout.write(self.style.SUCCESS("Successfully seeded catalog with 3 products, 10 variants, 3 categories, and 2 banners!"))
