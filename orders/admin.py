from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'created_at', 'delivery_phone')
    list_filter = ('status', 'created_at')
    search_fields = ('user__email', 'delivery_phone', 'delivery_address')
    inlines = [OrderItemInline]
    readonly_fields = ('created_at', 'updated_at')
