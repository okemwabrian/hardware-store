from django.contrib import admin
from .models import Category, Supplier, Product

admin.site.register(Category)
admin.site.register(Supplier)
admin.site.register(Product)