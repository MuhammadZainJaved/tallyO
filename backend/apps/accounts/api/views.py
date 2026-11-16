from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from apps.accounts.api.serializers import (
    CreateStaffUserSerializer,
    LoginSerializer,
    StaffUserSerializer,
)
from apps.core.permissions import IsSuperAdmin
from apps.stores.models import Store


User = get_user_model()


class LoginView(APIView):
    permission_classes = (AllowAny,)
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "login"

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, _ = Token.objects.get_or_create(user=user)
        stores = Store.objects.visible_to(user).values("id", "name", "slug")
        return Response(
            {
                "token": token.key,
                "user": StaffUserSerializer(user).data,
                "stores": list(stores),
            }
        )


class LogoutView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CurrentUserView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        stores = Store.objects.visible_to(request.user).values("id", "name", "slug")
        return Response(
            {
                "user": StaffUserSerializer(request.user).data,
                "stores": list(stores),
            }
        )


class StaffUserViewSet(ModelViewSet):
    permission_classes = (IsSuperAdmin,)
    http_method_names = ("get", "post", "patch", "head", "options")
    queryset = User.objects.all().order_by("email")

    def get_serializer_class(self):
        if self.action == "create":
            return CreateStaffUserSerializer
        return StaffUserSerializer

