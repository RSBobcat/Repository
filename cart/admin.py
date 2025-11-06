from django.contrib import admin
from .models import CartItem


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'product_size', 'quantity', 'total_price', 'created_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('user__username', 'product__name')
    readonly_fields = ('created_at', 'updated_at', 'total_price')
    
    def total_price(self, obj):
        return f"{obj.total_price:.2f} ₼"
    total_price.short_description = 'Total Price'
