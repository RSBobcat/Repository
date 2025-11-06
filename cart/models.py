from django.db import models
from django.contrib.auth.models import User
from main.models import Product, ProductSize


class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    product_size = models.ForeignKey(ProductSize, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'product', 'product_size')

    def __str__(self):
        return f"{self.quantity} x {self.product.name} ({self.product_size.size.name}) for {self.user.username}"

    @property
    def total_price(self):
        return self.quantity * self.product.price
