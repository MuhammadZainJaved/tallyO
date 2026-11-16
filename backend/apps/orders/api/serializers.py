from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.orders.models import Customer, Order, OrderItem
from apps.orders.services import CheckoutCommand, CheckoutItem, place_order


class CheckoutItemSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1, max_value=999)


class CheckoutSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=32)
    email = serializers.EmailField(allow_blank=True, required=False, default="")
    customer_name = serializers.CharField(max_length=150, allow_blank=True, required=False, default="")
    delivery_address = serializers.CharField(max_length=1000)
    delivery_latitude = serializers.DecimalField(
        max_digits=9, decimal_places=6, min_value=-90, max_value=90, required=False, allow_null=True
    )
    delivery_longitude = serializers.DecimalField(
        max_digits=9, decimal_places=6, min_value=-180, max_value=180, required=False, allow_null=True
    )
    notes = serializers.CharField(max_length=1000, allow_blank=True, required=False, default="")
    items = CheckoutItemSerializer(many=True, allow_empty=False)

    def validate(self, attrs):
        latitude = attrs.get("delivery_latitude")
        longitude = attrs.get("delivery_longitude")
        if (latitude is None) != (longitude is None):
            raise serializers.ValidationError(
                {"delivery_location": "Latitude and longitude must be supplied together."}
            )
        return attrs

    def create(self, validated_data):
        items = tuple(CheckoutItem(**item) for item in validated_data.pop("items"))
        command = CheckoutCommand(
            items=items,
            idempotency_key=self.context.get("idempotency_key", ""),
            **validated_data,
        )
        try:
            return place_order(store=self.context["store"], command=command)
        except DjangoValidationError as exc:
            details = exc.message_dict if hasattr(exc, "message_dict") else exc.messages
            raise serializers.ValidationError(details) from exc


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ("product_name", "sku", "unit_price", "quantity", "line_total")


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = (
            "id", "public_token", "status", "customer_name", "phone_snapshot", "email_snapshot",
            "delivery_address", "delivery_latitude", "delivery_longitude",
            "delivery_distance_miles", "notes", "currency", "subtotal", "delivery_fee", "total",
            "items", "created_at", "updated_at",
        )


class PublicOrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = (
            "public_token", "status", "customer_name", "currency", "subtotal",
            "delivery_fee", "total", "items", "created_at", "updated_at",
        )


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = (
            "id", "phone", "email", "name", "last_delivery_address",
            "order_count", "last_order_at",
        )
        read_only_fields = ("id", "phone", "order_count", "last_order_at")

    def validate_email(self, value):
        return value.strip().lower()


class TransitionOrderSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Order.Status.choices)

