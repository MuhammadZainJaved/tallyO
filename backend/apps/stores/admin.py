from django.contrib import admin

from apps.stores.models import Store, StoreBranding, StoreMembership


class StoreBrandingInline(admin.StackedInline):
    model = StoreBranding
    extra = 0
    max_num = 1


class StoreMembershipInline(admin.TabularInline):
    model = StoreMembership
    extra = 0


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "status", "timezone", "created_at")
    list_filter = ("status",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    inlines = (StoreBrandingInline, StoreMembershipInline)


@admin.register(StoreMembership)
class StoreMembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "store", "role", "is_active")
    list_filter = ("role", "is_active")
    search_fields = ("user__email", "store__name")

