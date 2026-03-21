from django.db import models
from django.shortcuts import render
from inventory.models import Product
from sales.models import Sale
from django.db.models import Sum, F

def dashboard(request):
    total_products = Product.objects.count()
    low_stock_items = Product.objects.filter(
        stock_quantity__lte=models.F('reorder_level')
    )
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