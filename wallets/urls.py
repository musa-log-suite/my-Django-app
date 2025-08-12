# wallets/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    WalletViewSet,
    TransactionViewSet,
    MyTokenObtainPairView,
    MyTokenRefreshView,
    MyTokenVerifyView,
    WalletBalanceView,
    TransactionHistoryView,
    export_dashboard_pdf,  # ← imported the PDF export view
)

router = DefaultRouter()
router.register(r'wallets', WalletViewSet, basename='wallet')
router.register(r'transactions', TransactionViewSet, basename='transaction')

urlpatterns = [
    # JWT Authentication endpoints
    path('token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', MyTokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', MyTokenVerifyView.as_view(), name='token_verify'),

    # Wallet balance & transaction-history endpoints
    path('wallet/balance/', WalletBalanceView.as_view(), name='wallet-balance'),
    path('transactions/history/', TransactionHistoryView.as_view(), name='transaction-history'),

    # PDF export endpoint
    path('export/dashboard/', export_dashboard_pdf, name='export_dashboard_pdf'),

    # ViewSet routes for wallets and transactions
    path('', include(router.urls)),
]