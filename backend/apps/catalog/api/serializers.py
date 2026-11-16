from rest_framework import serializers

from apps.catalog.models import Category, Product
from apps.stores.api.serializers import StoreBrandingSerializer
from apps.stores.models import Store


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = (
            "id", "name", "slug", "description", "display_order", "is_active",
            "created_at", "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def create(self, validated_data):
        return Category.objects.create(store=self.context["store"], **validated_data)


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    is_available = serializers.BooleanField(read_only=True)

    class Meta:
        model = Product
        fields = (
            "id", "category", "category_name", "name", "slug", "description", "sku",
            "price", "image_url", "is_active", "track_inventory", "stock_quantity",
            "is_available", "created_at", "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def validate_category(self, category):
        if category is not None and category.store_id != self.context["store"].id:
            raise serializers.ValidationError("Category must belong to the same store.")
        return category

    def create(self, validated_data):
        product = Product(store=self.context["store"], **validated_data)
        product.full_clean(exclude=("store",))
        product.save()
        return product

    def update(self, instance, validated_data):
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.full_clean()
        instance.save()
        return instance


class PublicCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "name", "slug", "description", "display_order")


class PublicProductSerializer(serializers.ModelSerializer):
    category = PublicCategorySerializer(read_only=True)
    is_available = serializers.BooleanField(read_only=True)

    class Meta:
        model = Product
        fields = (
            "id", "category", "name", "slug", "description", "price", "image_url",
            "is_available",
        )


class StorefrontConfigSerializer(serializers.ModelSerializer):
    branding = StoreBrandingSerializer(read_only=True)

    class Meta:
        model = Store
        fields = (
            "id", "name", "slug", "currency", "delivery_fee", "location_address",
            "latitude", "longitude", "delivery_radius_miles",
            "delivery_radius_enabled", "branding",
        )


class PublicProductDiscoverySerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    store_name = serializers.CharField(source="store.name", read_only=True)
    store_slug = serializers.CharField(source="store.slug", read_only=True)
    store_currency = serializers.CharField(source="store.currency", read_only=True)
    is_available = serializers.BooleanField(read_only=True)

    class Meta:
        model = Product
        fields = (
            "id", "name", "slug", "description", "price", "image_url",
            "category_name", "is_available", "store_name", "store_slug",
            "store_currency",
        )

