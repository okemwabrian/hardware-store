from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('search/', views.search_products, name='search'),
    path('restock/<int:product_id>/', views.restock_product, name='restock'),
]