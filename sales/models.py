from django.db import models
from inventory.models import Product
import random
import string


class Receipt(models.Model):
    receipt_number = models.CharField(max_length=20, unique=True, blank=True)
    date = models.DateTimeField(auto_now_add=True)
    served_by = models.CharField(max_length=100, blank=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        if not self.receipt_number:
            self.receipt_number = 'RCP-' + ''.join(random.choices(string.digits, k=6))
        super().save(*args, **kwargs)

    def __str__(self):
        return self.receipt_number


class Sale(models.Model):
    receipt = models.ForeignKey(Receipt, on_delete=models.CASCADE, null=True, blank=True, related_name='items')
    receipt_number = models.CharField(max_length=20, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity_sold = models.IntegerField()
    date = models.DateTimeField(auto_now_add=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.receipt_number:
            self.receipt_number = 'RCP-' + ''.join(random.choices(string.digits, k=6))
        self.total_price = self.product.price * self.quantity_sold
        self.product.stock_quantity -= self.quantity_sold
        self.product.save()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantity_sold} x {self.product.name}"