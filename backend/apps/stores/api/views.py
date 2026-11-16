from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import NotFound
from rest_framework.viewsets import ModelViewSet

from apps.core.permissions import IsSuperAdmin
from apps.stores.api.serializers import (
    StoreCreateSerializer,
    StoreMembershipSerializer,
    StoreReadSerializer,
    StoreUpdateSerializer,
)
from apps.stores.models import Store, StoreMembership


class StoreViewSet(ModelViewSet):
    http_method_names = ("get", "post", "patch", "head", "options")

    def get_queryset(self):
        return Store.objects.visible_to(self.request.user).select_related("branding")

    def get_permissions(self):
        permission_classes = [IsSuperAdmin] if self.action == "create" else [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        if self.action == "create":
            return StoreCreateSerializer
        if self.action in {"update", "partial_update"}:
            return StoreUpdateSerializer
        return StoreReadSerializer


class StoreMembershipViewSet(ModelViewSet):
    serializer_class = StoreMembershipSerializer
    http_method_names = ("get", "post", "patch", "head", "options")

    def get_store(self):
        if not hasattr(self, "_store"):
            try:
                self._store = Store.objects.visible_to(self.request.user).get(
                    id=self.kwargs["store_id"]
                )
            except Store.DoesNotExist as exc:
                raise NotFound("Store not found.") from exc
        return self._store

    def get_queryset(self):
        return StoreMembership.objects.filter(store=self.get_store()).select_related("user")

    def get_permissions(self):
        permission_classes = (
            [IsSuperAdmin]
            if self.action in {"create", "update", "partial_update"}
            else [IsAuthenticated]
        )
        return [permission() for permission in permission_classes]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["store"] = self.get_store()
        return context

