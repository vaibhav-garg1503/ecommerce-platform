from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect
from django.utils.html import format_html

from apps.catalog.models import Category, Product, ProductVariant, ProductImage


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0
    fields = ('sku', 'size', 'color', 'price', 'compare_at_price', 'stock_qty', 'low_stock_threshold', 'is_active')


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 0
    fields = ('image', 'variant', 'alt_text', 'sort_order')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'sort_order', 'is_active')
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ('is_active',)
    search_fields = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'brand', 'min_price_display', 'stock_status_badge', 'is_active', 'is_featured', 'created_at')
    list_filter = ('is_active', 'is_featured', 'category')
    search_fields = ('name', 'brand', 'variants__sku')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductVariantInline, ProductImageInline]
    change_list_template = "admin/catalog/product_change_list.html"

    def min_price_display(self, obj):
        min_price = obj.min_price
        return f"${min_price}" if min_price else "N/A"
    min_price_display.short_description = "Starting Price"

    def stock_status_badge(self, obj):
        variants = obj.variants.all()
        if not variants:
            return format_html('<span style="color: gray;">No variants</span>')
        out_of_stock = all(v.stock_qty <= 0 for v in variants)
        low_stock = any(v.stock_qty <= v.low_stock_threshold for v in variants)
        if out_of_stock:
            return format_html('<span style="color: red; font-weight: bold;">Out of Stock</span>')
        elif low_stock:
            return format_html('<span style="color: orange; font-weight: bold;">Low Stock</span>')
        return format_html('<span style="color: green;">In Stock</span>')
    stock_status_badge.short_description = "Stock Status"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('bulk-import/', self.admin_site.admin_view(self.bulk_import_redirect), name='catalog_product_bulk-import'),
            path('low-stock/', self.admin_site.admin_view(self.low_stock_redirect), name='catalog_product_low-stock'),
            path('sample-csv/', self.admin_site.admin_view(self.sample_csv_redirect), name='catalog_product_sample-csv'),
        ]
        return custom_urls + urls

    def bulk_import_redirect(self, request):
        return redirect('catalog:admin_bulk_import')

    def low_stock_redirect(self, request):
        return redirect('catalog:admin_low_stock')

    def sample_csv_redirect(self, request):
        return redirect('catalog:admin_sample_csv')


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'sku', 'price', 'stock_qty', 'stock_status', 'is_active')
    list_filter = ('is_active', 'product__category')
    search_fields = ('sku', 'product__name')
    actions = ['make_active', 'make_inactive']

    def stock_status(self, obj):
        if obj.stock_qty <= 0:
            return "Out of Stock"
        elif obj.stock_qty <= obj.low_stock_threshold:
            return "Low Stock"
        return "In Stock"

    @admin.action(description="Mark selected variants as active")
    def make_active(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description="Mark selected variants as inactive")
    def make_inactive(self, request, queryset):
        queryset.update(is_active=False)
