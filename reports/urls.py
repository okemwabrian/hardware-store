from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('search/', views.search_products, name='search'),
    path('restock/<int:product_id>/', views.restock_product, name='restock'),
    path('product/add/', views.add_product, name='add_product'),
    path('product/edit/<int:product_id>/', views.edit_product, name='edit_product'),
    path('product/delete/<int:product_id>/', views.delete_product, name='delete_product'),
    path('sale/record/', views.record_sale, name='record_sale'),
    path('sale/receipt/<int:sale_id>/', views.receipt, name='receipt'),
    path('sales/filter/', views.filter_sales, name='filter_sales'),
    path('report/print/', views.print_report, name='print_report'),
    path('settings/', views.settings_page, name='settings'),
]