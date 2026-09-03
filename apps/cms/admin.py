from django.contrib import admin
from .models import Page, Banner, Coupon


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'is_published', 'updated_at')
    list_filter = ('is_published',)
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ('title', 'content')


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ('title', 'sort_order', 'is_active')
    list_filter = ('is_active',)
    list_editable = ('sort_order', 'is_active')


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_type', 'discount_value', 'times_used', 'max_uses', 'is_active', 'valid_until')
    list_filter = ('discount_type', 'is_active')
    search_fields = ('code',)
    readonly_fields = ('times_used',)
