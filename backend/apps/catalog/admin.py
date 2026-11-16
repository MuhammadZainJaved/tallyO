from django.contrib import admin

from apps.catalog.models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "store", "display_order", "is_active")
    list_filter = ("store", "is_active")
    search_fields = ("name", "slug", "store__name")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "store", "category", "price", "stock_quantity", "is_active")
    list_filter = ("store", "is_active", "track_inventory")
    search_fields = ("name", "slug", "sku")

