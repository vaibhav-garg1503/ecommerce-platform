from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.urls import reverse
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.db.models import Min, Max, Q, F
from apps.catalog.models import Product, Category, ProductVariant
from apps.catalog.forms import BulkImportForm, RestockForm
from apps.catalog.services import BulkProductImporter
from apps.cms.models import Banner


def home_view(request):
    banners = Banner.objects.filter(is_active=True).order_by('sort_order')
    categories = Category.objects.filter(is_active=True).order_by('sort_order')
    featured_products = Product.objects.filter(is_featured=True, is_active=True)
    return render(request, 'catalog/home.html', {
        'banners': banners,
        'categories': categories,
        'featured_products': featured_products,
    })


def product_list_view(request, category_slug=None):
    qs = Product.objects.filter(is_active=True)

    if category_slug:
        qs = qs.filter(category__slug=category_slug)

    if request.GET.get('is_featured') == 'true':
        qs = qs.filter(is_featured=True)

    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(
            Q(name__icontains=q) |
            Q(brand__icontains=q) |
            Q(description__icontains=q) |
            Q(category__name__icontains=q)
        ).distinct()

    category_id = request.GET.get('category')
    if category_id:
        qs = qs.filter(category_id=category_id)

    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        qs = qs.filter(variants__price__gte=min_price).distinct()
    if max_price:
        qs = qs.filter(variants__price__lte=max_price).distinct()

    size = request.GET.get('size')
    if size:
        qs = qs.filter(variants__size=size).distinct()

    color = request.GET.get('color')
    if color:
        qs = qs.filter(variants__color=color).distinct()

    in_stock = request.GET.get('in_stock')
    if in_stock == 'true':
        qs = qs.filter(variants__stock_qty__gt=0).distinct()

    sort = request.GET.get('sort')
    if sort == 'price_asc':
        qs = qs.annotate(min_p=Min('variants__price')).order_by('min_p')
    elif sort == 'price_desc':
        qs = qs.annotate(max_p=Max('variants__price')).order_by('-max_p')
    elif sort == 'newest':
        qs = qs.order_by('-created_at')
    elif sort == 'name':
        qs = qs.order_by('name')

    all_categories = Category.objects.filter(is_active=True)
    all_sizes = (
    ProductVariant.objects
    .filter(product__is_active=True)
    .exclude(size__isnull=True)
    .exclude(size='')
    .values_list('size', flat=True)
)
    all_sizes = sorted(set(s.strip() for s in all_sizes if s and s.strip()))

    all_colors = (
    ProductVariant.objects
    .filter(product__is_active=True)
    .exclude(color__isnull=True)
    .exclude(color='')
    .values_list('color', flat=True)
)
    all_colors = sorted(set(c.strip() for c in all_colors if c and c.strip()))
    # all_sizes = ProductVariant.objects.filter(product__is_active=True).values_list('size', flat=True).distinct()
    # all_colors = ProductVariant.objects.filter(product__is_active=True).values_list('color', flat=True).distinct()
    # all_sizes = [s for s in all_sizes if s]
    # all_colors = [c for c in all_colors if c]

    paginator = Paginator(qs, 12)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    query_params = request.GET.copy()
    query_params.pop('page', None)

    context = {
        'page_obj': page_obj,
        'all_categories': all_categories,
        'all_sizes': all_sizes,
        'all_colors': all_colors,
        'current_category_slug': category_slug,
        'query_params': query_params.urlencode(),
    }

    if request.headers.get('HX-Request'):
        return render(request, 'catalog/partials/product_grid.html', context)
    return render(request, 'catalog/product_list.html', context)


def product_detail_view(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    variants = product.variants.filter(is_active=True)

    variant_id = request.GET.get('variant')
    if variant_id:
        default_variant = variants.filter(id=variant_id).first()
    else:
        default_variant = variants.filter(stock_qty__gt=0).first() or variants.first()

    sizes = variants.values_list('size', flat=True).distinct()
    colors = variants.values_list('color', flat=True).distinct()
    sizes = [s for s in sizes if s]
    colors = [c for c in colors if c]

    related_products = Product.objects.filter(category=product.category, is_active=True).exclude(id=product.id)[:4]

    context = {
        'product': product,
        'variants': variants,
        'default_variant': default_variant,
        'sizes': sizes,
        'colors': colors,
        'related_products': related_products,
    }
    return render(request, 'catalog/product_detail.html', context)


def search_autocomplete_view(request):
    q = request.GET.get('q', '').strip()
    if q:
        products = Product.objects.filter(
            Q(name__icontains=q) |
            Q(brand__icontains=q) |
            Q(category__name__icontains=q),
            is_active=True
        ).distinct()[:6]
    else:
        products = Product.objects.none()
    return render(request, 'catalog/partials/search_results.html', {'products': products})


def variant_info_api_view(request, variant_id):
    variant = get_object_or_404(ProductVariant, id=variant_id)
    return JsonResponse({
        'price': str(variant.price),
        'compare_at_price': str(variant.compare_at_price) if variant.compare_at_price else None,
        'stock_qty': variant.stock_qty,
        'in_stock': variant.is_in_stock,
        'is_low_stock': variant.is_low_stock,
    })


def sitemap_view(request):
    urls = []
    urls.append(request.build_absolute_uri(reverse('catalog:home')))
    urls.append(request.build_absolute_uri(reverse('catalog:product_list')))
    for cat in Category.objects.filter(is_active=True):
        urls.append(request.build_absolute_uri(reverse('catalog:category_detail', args=[cat.slug])))
    for prod in Product.objects.filter(is_active=True):
        urls.append(request.build_absolute_uri(reverse('catalog:product_detail', args=[prod.slug])))

    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for url in urls:
        xml += f'  <url>\n    <loc>{url}</loc>\n  </url>\n'
    xml += '</urlset>'
    return HttpResponse(xml, content_type='application/xml')


def robots_txt_view(request):
    try:
        sitemap_url = request.build_absolute_uri(reverse('catalog:sitemap'))
    except Exception:
        sitemap_url = "/sitemap.xml"
    content = f"User-agent: *\nAllow: /\nDisallow: /admin/\nSitemap: {sitemap_url}\n"
    return HttpResponse(content, content_type='text/plain')


@staff_member_required(login_url='admin:login')
def bulk_upload_admin_view(request):
    if request.method == 'POST':
        form = BulkImportForm(request.POST, request.FILES)
        if form.is_valid():
            result = BulkProductImporter.process_csv(form.cleaned_data['csv_file'])
            if result['errors']:
                for err in result['errors']:
                    messages.error(request, err)
            else:
                messages.success(
                    request,
                    f"Successfully imported {result['created_products']} new products and {result['created_variants']} variants."
                )
                return redirect('admin:catalog_product_changelist')
    else:
        form = BulkImportForm()
    return render(request, 'admin/catalog/bulk_import.html', {'form': form, 'title': 'Bulk Product CSV Import'})


@staff_member_required(login_url='admin:login')
def download_sample_csv_view(request):
    content = BulkProductImporter.generate_sample_csv()
    response = HttpResponse(content, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="sample_products_template.csv"'
    return response


@staff_member_required(login_url='admin:login')
def low_stock_report_admin_view(request):
    if request.method == 'POST':
        form = RestockForm(request.POST)
        if form.is_valid():
            variant = get_object_or_404(ProductVariant, id=form.cleaned_data['variant_id'])
            variant.stock_qty += form.cleaned_data['add_qty']
            variant.save()
            messages.success(request, f"Updated stock for {variant} (+{form.cleaned_data['add_qty']}). New stock: {variant.stock_qty}.")
            return redirect('catalog:admin_low_stock')

    low_stock_variants = ProductVariant.objects.filter(
        stock_qty__lte=F('low_stock_threshold'),
        is_active=True
    ).select_related('product', 'product__category')

    return render(request, 'admin/catalog/low_stock_report.html', {
        'variants': low_stock_variants,
        'title': 'Low Stock Inventory Alert Report'
    })
