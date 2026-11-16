from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers


User = get_user_model()


class StaffUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "full_name", "is_active", "is_superuser", "created_at")
        read_only_fields = ("id", "email", "is_superuser", "created_at")


class CreateStaffUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    is_superuser = serializers.BooleanField(default=False)

    class Meta:
        model = User
        fields = ("id", "email", "full_name", "password", "is_superuser")
        read_only_fields = ("id",)

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        is_superuser = validated_data.pop("is_superuser", False)
        return User.objects.create_user(
            password=password,
            is_superuser=is_superuser,
            is_staff=is_superuser,
            **validated_data,
        )


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        user = authenticate(
            request=self.context.get("request"),
            email=attrs["email"].lower(),
            password=attrs["password"],
        )
        if user is None or not user.is_active:
            raise serializers.ValidationError("Invalid email or password.")
        attrs["user"] = user
        return attrs

