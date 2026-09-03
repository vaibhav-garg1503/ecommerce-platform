import csv
import io
from decimal import Decimal, InvalidOperation
from typing import Dict, Any
from django.utils.text import slugify
from django.db import transaction
from apps.catalog.models import Category, Product, ProductVariant


class BulkProductImporter:
    """Service to handle bulk product imports from CSV files."""

    EXPECTED_HEADERS = [
        'category', 'product_name', 'brand', 'description', 'sku',
        'size', 'color', 'price', 'compare_at_price', 'stock_qty', 'low_stock_threshold'
    ]

    @classmethod
    def process_csv(cls, file_obj) -> Dict[str, Any]:
        """
        Reads CSV file and creates/updates categories, products, and variants.
        """
        result: Dict[str, Any] = {
            'created_products': 0,
            'created_variants': 0,
            'updated_variants': 0,
            'total_variants': 0,
            'errors': []
        }

        try:
            # Handle both string and bytes file objects
            content = file_obj.read()
            if isinstance(content, bytes):
                content = content.decode('utf-8-sig')

            csv_file = io.StringIO(content)
            reader = csv.DictReader(csv_file)

            if not reader.fieldnames:
                result['errors'].append("CSV file is empty or invalid.")
                return result

            # Convert headers to lowercase and strip whitespace
            headers = [h.strip().lower() for h in reader.fieldnames]
            reader.fieldnames = headers

            missing_headers = [h for h in cls.EXPECTED_HEADERS if h not in headers]
            if missing_headers:
                result['errors'].append(f"Missing required columns: {', '.join(missing_headers)}")
                return result

            with transaction.atomic():
                for line_num, row in enumerate(reader, start=2):
                    category_name = row.get('category', '').strip()
                    product_name = row.get('product_name', '').strip()
                    sku = row.get('sku', '').strip()
                    price_str = row.get('price', '').strip()

                    if not category_name:
                        result['errors'].append(f"Line {line_num}: Category name is required.")
                        continue
                    if not product_name:
                        result['errors'].append(f"Line {line_num}: Product name is required.")
                        continue
                    if not sku:
                        result['errors'].append(f"Line {line_num}: SKU is required.")
                        continue

                    try:
                        price = Decimal(price_str)
                        if price <= 0:
                            result['errors'].append(f"Line {line_num}: Price must be greater than 0.")
                            continue
                    except InvalidOperation:
                        result['errors'].append(f"Line {line_num}: Invalid price format.")
                        continue

                    # Handle optional fields with defaults
                    brand = row.get('brand', '').strip()
                    description = row.get('description', '').strip()
                    size = row.get('size', '').strip()
                    color = row.get('color', '').strip()

                    try:
                        compare_at_price = Decimal(row.get('compare_at_price', '').strip()) if row.get('compare_at_price', '').strip() else None
                    except InvalidOperation:
                        compare_at_price = None

                    try:
                        stock_qty = int(row.get('stock_qty', '0').strip() or '0')
                    except ValueError:
                        stock_qty = 0

                    try:
                        low_stock_threshold = int(row.get('low_stock_threshold', '5').strip() or '5')
                    except ValueError:
                        low_stock_threshold = 5

                    # Get or Create Category
                    category_slug = slugify(category_name)
                    category, _ = Category.objects.get_or_create(
                        slug=category_slug,
                        defaults={'name': category_name, 'is_active': True}
                    )

                    # Get or Create Product
                    product_slug = slugify(f"{brand} {product_name}" if brand else product_name)
                    product, p_created = Product.objects.get_or_create(
                        name=product_name,
                        category=category,
                        defaults={
                            'slug': product_slug,
                            'brand': brand,
                            'description': description,
                            'is_active': True
                        }
                    )
                    if p_created:
                        result['created_products'] += 1

                    # Update or Create Variant by SKU
                    variant, v_created = ProductVariant.objects.update_or_create(
                        sku=sku,
                        defaults={
                            'product': product,
                            'size': size,
                            'color': color,
                            'price': price,
                            'compare_at_price': compare_at_price,
                            'stock_qty': stock_qty,
                            'low_stock_threshold': low_stock_threshold,
                            'is_active': True
                        }
                    )
                    result['total_variants'] += 1
                    if v_created:
                        result['created_variants'] += 1
                    else:
                        result['updated_variants'] += 1

        except Exception as e:
            result['errors'].append(f"System Error: {str(e)}")

        return result

    @classmethod
    def generate_sample_csv(cls) -> str:
        """Returns a CSV string with standard headers and sample rows."""
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=cls.EXPECTED_HEADERS)
        writer.writeheader()
        writer.writerow({
            'category': 'Apparel',
            'product_name': 'Classic T-Shirt',
            'brand': 'Acme Corp',
            'description': 'A comfortable cotton t-shirt.',
            'sku': 'TSHIRT-RED-M',
            'size': 'M',
            'color': 'Red',
            'price': '19.99',
            'compare_at_price': '24.99',
            'stock_qty': '100',
            'low_stock_threshold': '10'
        })
        writer.writerow({
            'category': 'Apparel',
            'product_name': 'Classic T-Shirt',
            'brand': 'Acme Corp',
            'description': 'A comfortable cotton t-shirt.',
            'sku': 'TSHIRT-BLUE-L',
            'size': 'L',
            'color': 'Blue',
            'price': '19.99',
            'compare_at_price': '',
            'stock_qty': '5',
            'low_stock_threshold': '10'
        })
        return output.getvalue()
