from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum, F, Count
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import date
from inventory.models import Product, Category, Supplier
from sales.models import Sale

@login_required
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

@login_required
def search_products(request):
    query = request.GET.get('q', '')
    results = Product.objects.filter(
        name__icontains=query
    ) if query else Product.objects.none()
    return render(request, 'reports/search.html', {
        'query': query,
        'results': results,
    })

@login_required
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

@login_required
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

@login_required
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

@login_required
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        name = product.name
        product.delete()
        messages.success(request, f'"{name}" deleted!')
    return redirect('dashboard')

@login_required
def record_sale(request):
    products = Product.objects.all()
    if request.method == 'POST':
        product_id = request.POST.get('product')
        quantity = int(request.POST.get('quantity', 0))
        product = get_object_or_404(Product, id=product_id)

        if quantity <= 0:
            messages.error(request, 'Quantity must be greater than 0!')
            return redirect('record_sale')
        elif quantity > product.stock_quantity:
            messages.error(request, f'Not enough stock! Only {product.stock_quantity} units available.')
            return redirect('record_sale')
        else:
            sale = Sale.objects.create(product=product, quantity_sold=quantity)
            return redirect('receipt', sale_id=sale.id)

    return render(request, 'reports/record_sale.html', {'products': products})


@login_required
def receipt(request, sale_id):
    sale = get_object_or_404(Sale, id=sale_id)
    return render(request, 'reports/receipt.html', {'sale': sale})
@login_required
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

@login_required
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
@login_required
def settings_page(request):
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'change_password':
            from django.contrib.auth import update_session_auth_hash
            old_password = request.POST.get('old_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')

            if not request.user.check_password(old_password):
                messages.error(request, 'Current password is incorrect.')
            elif new_password != confirm_password:
                messages.error(request, 'New passwords do not match.')
            elif len(new_password) < 6:
                messages.error(request, 'Password must be at least 6 characters.')
            else:
                request.user.set_password(new_password)
                request.user.save()
                update_session_auth_hash(request, request.user)
                messages.success(request, 'Password changed successfully!')

    return render(request, 'reports/settings.html')


@login_required
def add_category(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            Category.objects.create(name=name)
            messages.success(request, f'Category "{name}" added!')
    return redirect('add_product')


@login_required
def delete_category(request, category_id):
    from inventory.models import Category
    cat = get_object_or_404(Category, id=category_id)
    if request.method == 'POST':
        cat.delete()
        messages.success(request, 'Category deleted!')
    return redirect('add_product')


@login_required
def add_supplier(request):
    if request.method == 'POST':
        Supplier.objects.create(
            name=request.POST.get('name'),
            phone=request.POST.get('phone', ''),
            email=request.POST.get('email', ''),
        )
        messages.success(request, f'Supplier "{request.POST.get("name")}" added!')
    return redirect('add_product')

@login_required
def add_product(request):
    categories = Category.objects.all()
    suppliers = Supplier.objects.all()

    if request.method == 'POST':
        form_type = request.POST.get('form_type')

        if form_type == 'add_product':
            name = request.POST.get('name')
            category_id = request.POST.get('category')
            supplier_id = request.POST.get('supplier')
            price = request.POST.get('price')
            stock_quantity = request.POST.get('stock_quantity')
            reorder_level = request.POST.get('reorder_level', 5)
            Product.objects.create(
                name=name,
                category_id=category_id if category_id else None,
                supplier_id=supplier_id if supplier_id else None,
                price=price,
                stock_quantity=stock_quantity,
                reorder_level=reorder_level,
            )
            messages.success(request, f'Product "{name}" added successfully!')

        elif form_type == 'add_category':
            name = request.POST.get('name')
            if name:
                Category.objects.create(name=name)
                messages.success(request, f'Category "{name}" added!')
            else:
                messages.error(request, 'Category name cannot be empty!')

        elif form_type == 'add_supplier':
            name = request.POST.get('name')
            if name:
                Supplier.objects.create(
                    name=name,
                    phone=request.POST.get('phone', ''),
                    email=request.POST.get('email', ''),
                )
                messages.success(request, f'Supplier "{name}" added!')
            else:
                messages.error(request, 'Supplier name cannot be empty!')

        return redirect('add_product')

    return render(request, 'reports/add_product.html', {
        'categories': categories,
        'suppliers': suppliers,
    })

@login_required
def delete_supplier(request, supplier_id):
    from inventory.models import Supplier
    sup = get_object_or_404(Supplier, id=supplier_id)
    if request.method == 'POST':
        sup.delete()
        messages.success(request, 'Supplier deleted!')
    return redirect('add_product')