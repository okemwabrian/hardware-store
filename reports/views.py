from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum, F
from django.db.models.functions import TruncDate
from inventory.models import Product, Category, Supplier
from sales.models import Sale


def dashboard(request):
    total_products = Product.objects.count()
    low_stock_items = Product.objects.filter(stock_quantity__lte=F('reorder_level'))
    recent_sales = Sale.objects.order_by('-date')[:10]
    total_sales_value = Sale.objects.aggregate(
        total=Sum('total_price')
    )['total'] or 0

    daily_sales = (
        Sale.objects.annotate(day=TruncDate('date'))
        .values('day')
        .annotate(total=Sum('total_price'))
        .order_by('day')
    )
    chart_labels = [str(entry['day']) for entry in daily_sales]
    chart_data = [float(entry['total']) for entry in daily_sales]

    all_products = Product.objects.select_related('category', 'supplier').all()
    categories = Category.objects.all()
    suppliers = Supplier.objects.all()

    context = {
        'total_products': total_products,
        'low_stock_items': low_stock_items,
        'recent_sales': recent_sales,
        'total_sales_value': total_sales_value,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
        'all_products': all_products,
        'categories': categories,
        'suppliers': suppliers,
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
        name = request.POST.get('name')
        category_id = request.POST.get('category')
        supplier_id = request.POST.get('supplier')
        price = request.POST.get('price')
        stock_quantity = request.POST.get('stock_quantity')
        reorder_level = request.POST.get('reorder_level', 5)

        Product.objects.create(
            name=name,
            category_id=category_id,
            supplier_id=supplier_id,
            price=price,
            stock_quantity=stock_quantity,
            reorder_level=reorder_level,
        )
        messages.success(request, f'Product "{name}" added successfully!')
        return redirect('dashboard')
    return render(request, 'reports/add_product.html', {
        'categories': categories,
        'suppliers': suppliers,
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
        messages.success(request, f'"{product.name}" updated successfully!')
        return redirect('dashboard')
    return render(request, 'reports/edit_product.html', {
        'product': product,
        'categories': categories,
        'suppliers': suppliers,
    })


def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        name = product.name
        product.delete()
        messages.success(request, f'"{name}" deleted successfully!')
    return redirect('dashboard')