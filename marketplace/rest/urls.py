# marketplace/rest/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BuyBundleView, ProductViewSet, PurchaseViewSet

app_name = 'marketplace_rest'

# DRF router for model viewsets
router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')
router.register(r'purchases', PurchaseViewSet, basename='purchase')

urlpatterns = [
    # POST /api/marketplace/rest/buy-bundle/
    path('buy-bundle/', BuyBundleView.as_view(), name='buy-bundle'),

    # GET /api/marketplace/rest/products/
    # GET /api/marketplace/rest/purchases/
    path('', include(router.urls)),
]