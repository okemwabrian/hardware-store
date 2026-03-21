from django.shortcuts import render
from django.db.models import Sum, F
from inventory.models import Product
from sales.models import Sale

def dashboard(request):
    total_products = Product.objects.count()
    low_stock_items = Product.objects.filter(stock_quantity__lte=F('reorder_level'))
    recent_sales = Sale.objects.order_by('-date')[:10]
    total_sales_value = Sale.objects.aggregate(
        total=Sum('total_price')
    )['total'] or 0

    context = {
        'total_products': total_products,
        'low_stock_items': low_stock_items,
        'recent_sales': recent_sales,
        'total_sales_value': total_sales_value,
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