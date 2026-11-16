from django.db.models import Q
from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from apps.catalog.api.serializers import (
    CategorySerializer,
    ProductSerializer,
    PublicCategorySerializer,
    PublicProductDiscoverySerializer,
    PublicProductSerializer,
    StorefrontConfigSerializer,
)
from apps.catalog.models import Category, Product
from apps.stores.models import Store


class StoreScopedViewSetMixin:
    permission_classes = (IsAuthenticated,)

    def get_store(self):
        if not hasattr(self, "_store"):
            self._store = get_object_or_404(
                Store.objects.visible_to(self.request.user),
                id=self.kwargs["store_id"],
            )
        return self._store

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["store"] = self.get_store()
        return context


class CategoryViewSet(StoreScopedViewSetMixin, ModelViewSet):
    serializer_class = CategorySerializer

    def get_queryset(self):
        return Category.objects.filter(store=self.get_store())


class ProductViewSet(StoreScopedViewSetMixin, ModelViewSet):
    serializer_class = ProductSerializer

    def get_queryset(self):
        queryset = Product.objects.filter(store=self.get_store()).select_related("category")
        category = self.request.query_params.get("category")
        if category:
            queryset = queryset.filter(category__slug=category)
        return queryset


def active_store(slug):
    return get_object_or_404(Store.objects.active(), slug=slug)


class PublicStoreDiscoveryView(ListAPIView):
    permission_classes = (AllowAny,)
    serializer_class = StorefrontConfigSerializer

    def get_queryset(self):
        queryset = Store.objects.active().select_related("branding")
        search = self.request.query_params.get("q", "").strip()
        if search:
            queryset = queryset.filter(Q(name__icontains=search) | Q(slug__icontains=search))
        return queryset


class PublicProductDiscoveryView(ListAPIView):
    permission_classes = (AllowAny,)
    serializer_class = PublicProductDiscoverySerializer

    def get_queryset(self):
        queryset = Product.objects.filter(store__status=Store.Status.ACTIVE, is_active=True).filter(
            Q(category__isnull=True) | Q(category__is_active=True)
        ).select_related("store", "category")
        search = self.request.query_params.get("q", "").strip()
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search)
                | Q(description__icontains=search)
                | Q(category__name__icontains=search)
                | Q(store__name__icontains=search)
            )
        return queryset


class StorefrontConfigView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, store_slug):
        store = active_store(store_slug)
        return Response(StorefrontConfigSerializer(store).data)


class PublicClientConfigView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        return Response(
            {
                "google_maps_enabled": bool(settings.GOOGLE_MAPS_BROWSER_API_KEY),
                "google_maps_browser_api_key": settings.GOOGLE_MAPS_BROWSER_API_KEY,
            }
        )


class PublicCategoryListView(ListAPIView):
    permission_classes = (AllowAny,)
    serializer_class = PublicCategorySerializer
    pagination_class = None

    def get_queryset(self):
        return Category.objects.filter(store=active_store(self.kwargs["store_slug"]), is_active=True)


class PublicProductListView(ListAPIView):
    permission_classes = (AllowAny,)
    serializer_class = PublicProductSerializer

    def get_queryset(self):
        store = active_store(self.kwargs["store_slug"])
        queryset = Product.objects.filter(store=store, is_active=True).filter(
            Q(category__isnull=True) | Q(category__is_active=True)
        ).select_related("category")
        category = self.request.query_params.get("category")
        search = self.request.query_params.get("q")
        if category:
            queryset = queryset.filter(category__slug=category)
        if search:
            queryset = queryset.filter(Q(name__icontains=search) | Q(description__icontains=search))
        return queryset


class PublicProductDetailView(RetrieveAPIView):
    permission_classes = (AllowAny,)
    serializer_class = PublicProductSerializer
    lookup_field = "slug"
    lookup_url_kwarg = "product_slug"

    def get_queryset(self):
        store = active_store(self.kwargs["store_slug"])
        return Product.objects.filter(store=store, is_active=True).filter(
            Q(category__isnull=True) | Q(category__is_active=True)
        ).select_related("category")

