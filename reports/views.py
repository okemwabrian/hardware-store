from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum, F, Count
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import date
from inventory.models import Product, Category, Supplier
from sales.models import Sale


def dashboard(request):
    total_products = Product.objects.count()
    low_stock_items = Product.objects.filter(stock_quantity__lte=F('reorder_level'))
    all_products = Product.objects.select_related('category', 'supplier').all()
    categories = Category.objects.all()
    suppliers = Supplier.objects.all()

    # Today's sales only
    today = date.today()
    today_sales = Sale.objects.filter(date__date=today)
    today_revenue = today_sales.aggregate(total=Sum('total_price'))['total'] or 0
    today_items_sold = today_sales.aggregate(total=Sum('quantity_sold'))['total'] or 0

    # All time total
    total_sales_value = Sale.objects.aggregate(total=Sum('total_price'))['total'] or 0

    # Recent sales
    recent_sales = Sale.objects.order_by('-date')[:10]

    # Daily breakdown
    daily_breakdown = (
        Sale.objects.annotate(day=TruncDate('date'))
        .values('day')
        .annotate(
            revenue=Sum('total_price'),
            items_sold=Sum('quantity_sold'),
            transactions=Count('id')
        )
        .order_by('-day')[:14]
    )

    # Chart data
    chart_data_qs = list(reversed(list(daily_breakdown)))
    chart_labels = [str(entry['day']) for entry in chart_data_qs]
    chart_data = [float(entry['revenue']) for entry in chart_data_qs]

    context = {
        'total_products': total_products,
        'low_stock_items': low_stock_items,
        'all_products': all_products,
        'categories': categories,
        'suppliers': suppliers,
        'today_revenue': today_revenue,
        'today_items_sold': today_items_sold,
        'total_sales_value': total_sales_value,
        'recent_sales': recent_sales,
        'daily_breakdown': daily_breakdown,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
        'today': today,
    }
    return render(request, 'reports/dashboard.html', context)


def search_products(request):
    query = request.GET.get('q', '')
    results = Product.objects.filter(
        name__icontains=query
    ) if query else Product.objects.none()
    return render(request, 'reports/search.html', {
        'query': query,
        'results': results,
    })


def restock_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 0))
        if quantity > 0:
            product.stock_quantity += quantity
            product.save()
            messages.success(request, f'{product.name} restocked by {quantity} units!')
        return redirect('dashboard')
    return render(request, 'reports/restock.html', {'product': product})


def add_product(request):
    categories = Category.objects.all()
    suppliers = Supplier.objects.all()
    if request.method == 'POST':
        Product.objects.create(
            name=request.POST.get('name'),
            category_id=request.POST.get('category'),
            supplier_id=request.POST.get('supplier'),
            price=request.POST.get('price'),
            stock_quantity=request.POST.get('stock_quantity'),
            reorder_level=request.POST.get('reorder_level', 5),
        )
        messages.success(request, f'Product "{request.POST.get("name")}" added!')
        return redirect('dashboard')
    return render(request, 'reports/add_product.html', {
        'categories': categories, 'suppliers': suppliers
    })


def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    categories = Category.objects.all()
    suppliers = Supplier.objects.all()
    if request.method == 'POST':
        product.name = request.POST.get('name')
        product.category_id = request.POST.get('category')
        product.supplier_id = request.POST.get('supplier')
        product.price = request.POST.get('price')
        product.stock_quantity = request.POST.get('stock_quantity')
        product.reorder_level = request.POST.get('reorder_level')
        product.save()
        messages.success(request, f'"{product.name}" updated!')
        return redirect('dashboard')
    return render(request, 'reports/edit_product.html', {
        'product': product, 'categories': categories, 'suppliers': suppliers
    })


def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        name = product.name
        product.delete()
        messages.success(request, f'"{name}" deleted!')
    return redirect('dashboard')


def record_sale(request):
    products = Product.objects.all()
    if request.method == 'POST':
        product_id = request.POST.get('product')
        quantity = int(request.POST.get('quantity', 0))
        product = get_object_or_404(Product, id=product_id)

        if quantity <= 0:
            messages.error(request, 'Quantity must be greater than 0!')
        elif quantity > product.stock_quantity:
            messages.error(request, f'Not enough stock! Only {product.stock_quantity} units available.')
        else:
            Sale.objects.create(product=product, quantity_sold=quantity)
            messages.success(request, f'Sale recorded — {quantity} x {product.name}!')
        return redirect('dashboard')
    return render(request, 'reports/record_sale.html', {'products': products})


def filter_sales(request):
    sales = Sale.objects.all().order_by('-date')
    products = Product.objects.all()

    # Filters
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    product_id = request.GET.get('product')

    if date_from:
        sales = sales.filter(date__date__gte=date_from)
    if date_to:
        sales = sales.filter(date__date__lte=date_to)
    if product_id:
        sales = sales.filter(product_id=product_id)

    total = sales.aggregate(total=Sum('total_price'))['total'] or 0
    items = sales.aggregate(total=Sum('quantity_sold'))['total'] or 0

    return render(request, 'reports/filter_sales.html', {
        'sales': sales,
        'products': products,
        'total': total,
        'items': items,
        'date_from': date_from or '',
        'date_to': date_to or '',
        'selected_product': product_id or '',
    })


def print_report(request):
    today = date.today()
    date_from = request.GET.get('date_from', str(today))
    date_to = request.GET.get('date_to', str(today))

    # Clean the date format — force YYYY-MM-DD
    try:
        from datetime import datetime
        # Handle cases where date might come in wrong format
        if '-' not in date_from:
            date_from = str(today)
        if '-' not in date_to:
            date_to = str(today)
    except Exception:
        date_from = str(today)
        date_to = str(today)

    sales = Sale.objects.filter(
        date__date__gte=date_from,
        date__date__lte=date_to
    ).order_by('date')

    total_revenue = sales.aggregate(total=Sum('total_price'))['total'] or 0
    total_items = sales.aggregate(total=Sum('quantity_sold'))['total'] or 0

    daily = (
        sales.annotate(day=TruncDate('date'))
        .values('day')
        .annotate(revenue=Sum('total_price'), items=Sum('quantity_sold'))
        .order_by('day')
    )

    return render(request, 'reports/print_report.html', {
        'sales': sales,
        'total_revenue': total_revenue,
        'total_items': total_items,
        'daily': daily,
        'date_from': date_from,
        'date_to': date_to,
    })