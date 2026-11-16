from django.core.exceptions import ValidationError as DjangoValidationError
from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers

from apps.accounts.api.serializers import StaffUserSerializer
from apps.stores.models import Store, StoreBranding, StoreMembership
from apps.stores.services import CreateStoreCommand, create_store


class StoreBrandingSerializer(serializers.ModelSerializer):
    class Meta:
        model = StoreBranding
        fields = ("logo_url", "banner_url", "primary_color", "secondary_color", "footer_text")


class StoreReadSerializer(serializers.ModelSerializer):
    branding = StoreBrandingSerializer(read_only=True)

    class Meta:
        model = Store
        fields = (
            "id", "name", "slug", "status", "timezone", "currency",
            "delivery_fee", "location_address", "latitude", "longitude",
            "delivery_radius_miles", "delivery_radius_enabled", "branding",
            "created_at", "updated_at",
        )


class StoreCreateSerializer(serializers.ModelSerializer):
    admin_email = serializers.EmailField(write_only=True, required=False)

    class Meta:
        model = Store
        fields = (
            "id", "name", "slug", "timezone", "currency", "delivery_fee",
            "location_address", "latitude", "longitude", "delivery_radius_miles",
            "delivery_radius_enabled", "admin_email",
        )
        read_only_fields = ("id",)

    def create(self, validated_data):
        command = CreateStoreCommand(**validated_data)
        try:
            return create_store(command=command, actor=self.context["request"].user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict) from exc

    def validate(self, attrs):
        latitude = attrs.get("latitude")
        longitude = attrs.get("longitude")
        if (latitude is None) != (longitude is None):
            raise serializers.ValidationError("Latitude and longitude must be supplied together.")
        if attrs.get("delivery_radius_enabled") and latitude is None:
            raise serializers.ValidationError(
                {"delivery_radius_enabled": "Set the store marker before enabling the delivery radius."}
            )
        return attrs


class StoreUpdateSerializer(serializers.ModelSerializer):
    branding = StoreBrandingSerializer(required=False)

    class Meta:
        model = Store
        fields = (
            "name", "timezone", "currency", "delivery_fee", "location_address",
            "latitude", "longitude", "delivery_radius_miles",
            "delivery_radius_enabled", "branding",
        )

    def validate(self, attrs):
        latitude = attrs.get("latitude", self.instance.latitude)
        longitude = attrs.get("longitude", self.instance.longitude)
        enabled = attrs.get("delivery_radius_enabled", self.instance.delivery_radius_enabled)
        if (latitude is None) != (longitude is None):
            raise serializers.ValidationError("Latitude and longitude must be supplied together.")
        if enabled and latitude is None:
            raise serializers.ValidationError(
                {"delivery_radius_enabled": "Set the store marker before enabling the delivery radius."}
            )
        return attrs

    @transaction.atomic
    def update(self, instance, validated_data):
        branding_data = validated_data.pop("branding", None)
        instance = super().update(instance, validated_data)
        if branding_data is not None:
            StoreBranding.objects.update_or_create(store=instance, defaults=branding_data)
        return instance


User = get_user_model()


class StoreMembershipSerializer(serializers.ModelSerializer):
    user = StaffUserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        source="user",
        queryset=User.objects.filter(is_active=True),
        write_only=True,
    )

    class Meta:
        model = StoreMembership
        fields = ("id", "user", "user_id", "role", "is_active", "created_at")
        read_only_fields = ("id", "role", "created_at")

    def validate(self, attrs):
        user = attrs.get("user")
        store = self.context["store"]
        if user and StoreMembership.objects.filter(store=store, user=user).exclude(
            pk=getattr(self.instance, "pk", None)
        ).exists():
            raise serializers.ValidationError({"user_id": "This user is already assigned to the store."})
        return attrs

    def create(self, validated_data):
        return StoreMembership.objects.create(
            store=self.context["store"],
            role=StoreMembership.Role.ADMIN,
            **validated_data,
        )


