from django.urls import path
from . import views

app_name = 'catalog'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('shop/', views.product_list_view, name='product_list'),
    path('category/<slug:category_slug>/', views.product_list_view, name='category_detail'),
    path('product/<slug:slug>/', views.product_detail_view, name='product_detail'),
    path('search/autocomplete/', views.search_autocomplete_view, name='search_autocomplete'),
    path('api/variant/<int:variant_id>/', views.variant_info_api_view, name='variant_info'),
    path('catalog-admin/bulk-import/', views.bulk_upload_admin_view, name='admin_bulk_import'),
    path('catalog-admin/sample-csv/', views.download_sample_csv_view, name='admin_sample_csv'),
    path('catalog-admin/low-stock/', views.low_stock_report_admin_view, name='admin_low_stock'),
    path('sitemap.xml', views.sitemap_view, name='sitemap'),
    path('robots.txt', views.robots_txt_view, name='robots'),
]

