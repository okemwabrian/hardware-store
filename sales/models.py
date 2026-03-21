from django.db import models
from inventory.models import Product

class Sale(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity_sold = models.IntegerField()
    date = models.DateTimeField(auto_now_add=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True)

    def save(self, *args, **kwargs):
        self.total_price = self.product.price * self.quantity_sold
        self.product.stock_quantity -= self.quantity_sold
        self.product.save()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantity_sold} x {self.product.name} on {self.date}"