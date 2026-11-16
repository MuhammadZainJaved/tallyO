from django.core.exceptions import ValidationError as DjangoValidationError
from django.shortcuts import get_object_or_404
from rest_framework import mixins, status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.orders.api.serializers import (
    CheckoutSerializer,
    CustomerSerializer,
    OrderSerializer,
    PublicOrderSerializer,
    TransitionOrderSerializer,
)
from apps.orders.models import Customer, Order
from apps.orders.services import transition_order
from apps.stores.models import Store


class CheckoutView(APIView):
    permission_classes = (AllowAny,)
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "checkout"

    def post(self, request, store_slug):
        store = get_object_or_404(Store.objects.active(), slug=store_slug)
        idempotency_key = request.headers.get("Idempotency-Key", "").strip()
        if len(idempotency_key) > 64:
            return Response(
                {"error": {"status": 400, "details": {"idempotency_key": ["Maximum length is 64."]}}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = CheckoutSerializer(
            data=request.data,
            context={"store": store, "idempotency_key": idempotency_key},
        )
        serializer.is_valid(raise_exception=True)
        order, created = serializer.save()
        order = Order.objects.prefetch_related("items").get(pk=order.pk)
        return Response(
            PublicOrderSerializer(order).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class PublicOrderDetailView(APIView):
    permission_classes = (AllowAny,)
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "order_lookup"

    def get(self, request, store_slug, public_token):
        order = get_object_or_404(
            Order.objects.prefetch_related("items"),
            store__slug=store_slug,
            store__status=Store.Status.ACTIVE,
            public_token=public_token,
        )
        return Response(PublicOrderSerializer(order).data)


class StoreScopedReadViewSetMixin:
    permission_classes = (IsAuthenticated,)

    def get_store(self):
        if not hasattr(self, "_store"):
            self._store = get_object_or_404(
                Store.objects.visible_to(self.request.user),
                id=self.kwargs["store_id"],
            )
        return self._store


class CustomerViewSet(
    StoreScopedReadViewSetMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = CustomerSerializer

    def get_queryset(self):
        return Customer.objects.filter(store=self.get_store())


class OrderViewSet(
    StoreScopedReadViewSetMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = OrderSerializer

    def get_queryset(self):
        queryset = Order.objects.filter(store=self.get_store()).select_related("customer").prefetch_related("items")
        order_status = self.request.query_params.get("status")
        if order_status:
            queryset = queryset.filter(status=order_status)
        return queryset

    def transition(self, request, *args, **kwargs):
        order = self.get_object()
        serializer = TransitionOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            order = transition_order(order=order, target_status=serializer.validated_data["status"])
        except DjangoValidationError as exc:
            details = exc.message_dict if hasattr(exc, "message_dict") else exc.messages
            return Response({"error": {"status": 400, "details": details}}, status=400)
        order = self.get_queryset().get(pk=order.pk)
        return Response(OrderSerializer(order).data)

