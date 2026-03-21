from django.shortcuts import render
from django.db.models import Sum, F
from inventory.models import Product
from sales.models import Sale
from django.db.models.functions import TruncDate

def dashboard(request):
    total_products = Product.objects.count()
    low_stock_items = Product.objects.filter(stock_quantity__lte=F('reorder_level'))
    recent_sales = Sale.objects.order_by('-date')[:10]
    total_sales_value = Sale.objects.aggregate(
        total=Sum('total_price')
    )['total'] or 0

    # Chart data - sales per day
    daily_sales = (
        Sale.objects.annotate(day=TruncDate('date'))
        .values('day')
        .annotate(total=Sum('total_price'))
        .order_by('day')
    )
    chart_labels = [str(entry['day']) for entry in daily_sales]
    chart_data = [float(entry['total']) for entry in daily_sales]

    context = {
        'total_products': total_products,
        'low_stock_items': low_stock_items,
        'recent_sales': recent_sales,
        'total_sales_value': total_sales_value,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
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