from django.urls import path, include
from rest_framework.routers import DefaultRouter
from marketplace.rest.views import (
    ProductViewSet,
    PurchaseViewSet,
    CategoryViewSet,
    ProviderViewSet,
    PopularProductViewSet,
)

# Set up router and register all ViewSets
router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')                # /products/
router.register(r'purchases', PurchaseViewSet, basename='purchase')            # /purchases/
router.register(r'categories', CategoryViewSet, basename='category')           # /categories/
router.register(r'providers', ProviderViewSet, basename='provider')            # /providers/
router.register(r'products/popular', PopularProductViewSet, basename='popular')  # /products/popular/

# URL patterns
urlpatterns = [
    path('', include(router.urls)),
]