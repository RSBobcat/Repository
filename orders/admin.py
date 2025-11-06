from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ('image_preview', 'product', 'product_size', 'quantity',
              'price', 'total_price')
    readonly_fields = ('image_preview', 'total_price')
    can_delete = False

    def image_preview(self, obj):
        if obj.product.image:
            return mark_safe(f'<img src="{obj.product.image.url}" style="max-height: 100px; max-width: 100px; object-fit: cover;" />')
        return mark_safe('<span style="color: gray;">No Image</span>')
    image_preview.short_description = 'Image'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_full_name', 'email',
                    'total_amount', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('email', 'first_name', 'last_name')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at', 'total_amount')
    inlines = [OrderItemInline]

    fieldsets = (
        ('Order Information', {
            'fields': ('user', 'first_name', 'last_name', 'email', 
                       'phone', 'address1', 'city', 'special_instructions', 'total_amount')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    get_full_name.short_description = 'Full Name'

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ('user', 'first_name', 'last_name', 'email', 
                                            'phone', 'address1', 'city')
        return self.readonly_fields