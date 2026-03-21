from django.contrib import admin
from .models import Sale

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ['product', 'quantity_sold', 'total_price', 'date']
    list_filter = ['date']
    search_fields = ['product__name']