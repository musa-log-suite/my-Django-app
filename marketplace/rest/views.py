from rest_framework import status, viewsets, permissions, filters
from rest_framework.views import APIView
from rest_framework.response import Response

from marketplace.models import Product, Purchase, Category
from wallets.models import Transaction
from marketplace.rest.serializers import (
    BuyBundleSerializer,
    ProductSerializer,
    PurchaseSerializer,
    CategorySerializer
)


class BuyBundleView(APIView):
    """
    POST /api/marketplace/rest/buy-bundle/
    Purchase a bundle by debiting the authenticated user’s wallet.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = BuyBundleSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        transaction = serializer.save()

        return Response({
            "message": "Bundle purchased successfully",
            "transaction_id": transaction.id,
            "product": transaction.bundle.name,
            "amount": f"₦{transaction.amount}",
            "timestamp": transaction.timestamp,
        }, status=status.HTTP_201_CREATED)


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/products/
    List & retrieve active airtime and data bundles.
    """
    queryset = Product.objects.filter(active=True)
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['provider', 'product_type', 'name']
    ordering_fields = ['provider', 'value', 'price']
    ordering = ['provider', 'value']


class PopularProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/products/popular/
    Returns bundles flagged as popular.
    """
    queryset = Product.objects.filter(active=True, popular=True)
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['value', 'price']
    ordering = ['-value']


class PurchaseViewSet(viewsets.ModelViewSet):
    """
    GET /api/purchases/ → list user's purchases
    POST /api/purchases/ → buy a bundle
    """
    serializer_class = PurchaseSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['timestamp', 'amount']
    ordering = ['-timestamp']

    def get_queryset(self):
        return Purchase.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/categories/
    List available product categories (e.g. Data, Airtime, SMS).
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]


class ProviderViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/providers/
    Grouped product listing by provider type (MTN, GLO, etc).
    """
    queryset = Product.objects.filter(active=True)
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = ['provider']