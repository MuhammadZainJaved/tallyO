from django.contrib import admin

from apps.orders.models import Customer, Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product", "product_name", "sku", "unit_price", "quantity", "line_total")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "store", "status", "phone_snapshot", "email_snapshot", "total", "created_at")
    list_filter = ("store", "status")
    search_fields = ("id", "phone_snapshot", "email_snapshot", "customer_name")
    inlines = (OrderItemInline,)


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("phone", "email", "name", "store", "order_count", "last_order_at")
    list_filter = ("store",)
    search_fields = ("phone", "email", "name")

