from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.accounts.api.views import CurrentUserView, LoginView, LogoutView, StaffUserViewSet
from apps.catalog.api.views import (
    CategoryViewSet,
    ProductViewSet,
    PublicCategoryListView,
    PublicClientConfigView,
    PublicProductDetailView,
    PublicProductDiscoveryView,
    PublicProductListView,
    PublicStoreDiscoveryView,
    StorefrontConfigView,
)
from apps.core.views import HealthCheckView
from apps.orders.api.views import CheckoutView, CustomerViewSet, OrderViewSet, PublicOrderDetailView
from apps.reporting.api.views import DailyOrderReportViewSet
from apps.stores.api.views import StoreMembershipViewSet, StoreViewSet

router = DefaultRouter()
router.register("stores", StoreViewSet, basename="store")
router.register("users", StaffUserViewSet, basename="user")
router.register("reports/daily-orders", DailyOrderReportViewSet, basename="daily-order-report")

membership_list = StoreMembershipViewSet.as_view({"get": "list", "post": "create"})
membership_detail = StoreMembershipViewSet.as_view(
    {"get": "retrieve", "patch": "partial_update"}
)
category_list = CategoryViewSet.as_view({"get": "list", "post": "create"})
category_detail = CategoryViewSet.as_view(
    {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
)
product_list = ProductViewSet.as_view({"get": "list", "post": "create"})
product_detail = ProductViewSet.as_view(
    {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
)
customer_list = CustomerViewSet.as_view({"get": "list"})
customer_detail = CustomerViewSet.as_view({"get": "retrieve", "patch": "partial_update"})
order_list = OrderViewSet.as_view({"get": "list"})
order_detail = OrderViewSet.as_view({"get": "retrieve"})
order_transition = OrderViewSet.as_view({"post": "transition"})

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", HealthCheckView.as_view(), name="health-check"),
    path("api/v1/auth/login/", LoginView.as_view(), name="login"),
    path("api/v1/auth/logout/", LogoutView.as_view(), name="logout"),
    path("api/v1/auth/me/", CurrentUserView.as_view(), name="current-user"),
    path("api/v1/config/public/", PublicClientConfigView.as_view(), name="public-client-config"),
    path("api/v1/storefront/<slug:store_slug>/", StorefrontConfigView.as_view(), name="storefront-config"),
    path("api/v1/storefronts/", PublicStoreDiscoveryView.as_view(), name="public-store-discovery"),
    path("api/v1/products/search/", PublicProductDiscoveryView.as_view(), name="public-product-discovery"),
    path("api/v1/storefront/<slug:store_slug>/categories/", PublicCategoryListView.as_view(), name="public-category-list"),
    path("api/v1/storefront/<slug:store_slug>/products/", PublicProductListView.as_view(), name="public-product-list"),
    path("api/v1/storefront/<slug:store_slug>/products/<slug:product_slug>/", PublicProductDetailView.as_view(), name="public-product-detail"),
    path("api/v1/storefront/<slug:store_slug>/orders/", CheckoutView.as_view(), name="checkout"),
    path("api/v1/storefront/<slug:store_slug>/orders/<uuid:public_token>/", PublicOrderDetailView.as_view(), name="public-order-detail"),
    path(
        "api/v1/stores/<uuid:store_id>/memberships/",
        membership_list,
        name="store-membership-list",
    ),
    path(
        "api/v1/stores/<uuid:store_id>/memberships/<uuid:pk>/",
        membership_detail,
        name="store-membership-detail",
    ),
    path("api/v1/stores/<uuid:store_id>/categories/", category_list, name="category-list"),
    path("api/v1/stores/<uuid:store_id>/categories/<uuid:pk>/", category_detail, name="category-detail"),
    path("api/v1/stores/<uuid:store_id>/products/", product_list, name="product-list"),
    path("api/v1/stores/<uuid:store_id>/products/<uuid:pk>/", product_detail, name="product-detail"),
    path("api/v1/stores/<uuid:store_id>/customers/", customer_list, name="customer-list"),
    path("api/v1/stores/<uuid:store_id>/customers/<uuid:pk>/", customer_detail, name="customer-detail"),
    path("api/v1/stores/<uuid:store_id>/orders/", order_list, name="order-list"),
    path("api/v1/stores/<uuid:store_id>/orders/<uuid:pk>/", order_detail, name="order-detail"),
    path("api/v1/stores/<uuid:store_id>/orders/<uuid:pk>/transition/", order_transition, name="order-transition"),
    path("api/v1/", include(router.urls)),
]

