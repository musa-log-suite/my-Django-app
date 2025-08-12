from rest_framework import viewsets, permissions, filters, serializers
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.throttling import UserRateThrottle
from rest_framework.decorators import api_view
from django.db.models import Count
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Product, Purchase
from .serializers import (
    ProductSerializer,
    PurchaseSerializer,
    ProviderSerializer,
    CategorySerializer,
    PopularProductSerializer,
)

# 🔧 Base settings reused across views
BASE_PERMISSION_CLASSES = [permissions.IsAuthenticatedOrReadOnly]
BASE_THROTTLE_CLASSES = [UserRateThrottle]
BASE_PAGINATION_CLASS = PageNumberPagination

# 🧪 Optional mock wallet response
@swagger_auto_schema(
    method='get',
    operation_summary="Mock Wallet Sample",
    operation_description="Returns a static wallet payload for frontend testing.",
    responses={
        200: openapi.Response(
            description="Mock wallet structure",
            examples={
                "application/json": {
                    "id": 1,
                    "owner": "demo_user",
                    "balance": 25000,
                    "currency": "USD",
                    "status": "active",
                }
            },
        ),
    }
)
@api_view(['GET'])
def mock_wallet_sample(request):
    sample = {
        "id": 1,
        "owner": "demo_user",
        "balance": 25000,
        "currency": "USD",
        "status": "active",
    }
    return Response(sample)


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    List & retrieve available airtime and data bundles.
    GET /products/ → all active bundles
    """
    queryset = Product.objects.filter(active=True)
    serializer_class = ProductSerializer
    permission_classes = BASE_PERMISSION_CLASSES
    pagination_class = BASE_PAGINATION_CLASS
    throttle_classes = BASE_THROTTLE_CLASSES
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['provider', 'product_type', 'name']
    ordering_fields = ['provider', 'value', 'price']
    ordering = ['provider', 'value']


class PurchaseViewSet(viewsets.ModelViewSet):
    """
    Handles product purchases.
    - GET /purchases/        → List user’s purchases (newest first)
    - GET /purchases/{id}/   → Retrieve purchase detail
    - POST /purchases/       → Make a new purchase
    """
    serializer_class = PurchaseSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = BASE_PAGINATION_CLASS
    throttle_classes = BASE_THROTTLE_CLASSES
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['timestamp', 'amount']
    ordering = ['-timestamp']

    def get_queryset(self):
        return Purchase.objects.filter(user=self.request.user).order_by('-timestamp')

    def perform_create(self, serializer):
        try:
            serializer.save(user=self.request.user)
        except Exception as e:
            raise serializers.ValidationError({"error": str(e)})


class ProviderViewSet(viewsets.ViewSet):
    """
    Return list of unique providers.
    GET /providers/ → ["mtn", "airtel", "glo", ...]
    """
    permission_classes = BASE_PERMISSION_CLASSES
    throttle_classes = BASE_THROTTLE_CLASSES

    def list(self, request):
        providers = Product.objects.values_list('provider', flat=True).distinct()
        data = [{'id': p, 'name': p.upper()} for p in providers]
        return Response(data)


class CategoryViewSet(viewsets.ViewSet):
    """
    Return available product categories.
    GET /categories/ → ["airtime", "data"]
    """
    permission_classes = BASE_PERMISSION_CLASSES
    throttle_classes = BASE_THROTTLE_CLASSES

    def list(self, request):
        categories = Product.objects.values_list('product_type', flat=True).distinct()
        data = [{'id': c, 'label': c.title()} for c in categories]
        return Response(data)


class PopularProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    List top-selling products based on purchase count.
    GET /products/popular/ → Ranked bundles
    """
    permission_classes = BASE_PERMISSION_CLASSES
    throttle_classes = BASE_THROTTLE_CLASSES
    pagination_class = BASE_PAGINATION_CLASS
    serializer_class = PopularProductSerializer

    def get_queryset(self):
        return Product.objects.filter(active=True)\
            .annotate(purchase_count=Count('purchases'))\
            .order_by('-purchase_count')