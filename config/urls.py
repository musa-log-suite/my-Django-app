from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.views.generic import TemplateView

from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.permissions import AllowAny

from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from wallets.admin_site import custom_admin_site
from wallets.views import WalletViewSet, TransactionViewSet, monnify_webhook  # ✅ Monnify webhook imported
from marketplace.views import mock_wallet_sample

from config.views import (
    home,
    status_check,
    metadata_overview,
    dashboard_overview,
    version_info,
    agent_dashboard,
    secure_view,
    SecureDashboardView,
    SecureDashboardAPI,
)

from config.permissions import IsAdminUserSwaggerOnly

# 🔁 DRF Router setup
router = DefaultRouter()
router.register(r"wallet", WalletViewSet, basename="wallet")
router.register(r"transactions", TransactionViewSet, basename="transaction")

# 🔐 Admin-only Swagger (internal API)
admin_schema_view = get_schema_view(
    openapi.Info(
        title="🪙 Wallet API",
        default_version="v1",
        description="Secure Wallet and Marketplace API",
        terms_of_service="https://yourdomain.com/terms/",
        contact=openapi.Contact(email="support@yourdomain.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=False,
    permission_classes=[IsAdminUserSwaggerOnly],
)

# 🌐 Public Swagger (user auth API)
user_auth_schema_view = get_schema_view(
    openapi.Info(
        title="User Auth API",
        default_version="v1",
        description="User registration, OTP, and recovery flows",
    ),
    public=True,
    permission_classes=[AllowAny],
)

# 🌍 URL patterns
urlpatterns = [
    # 📌 System Info & Core Views
    path("system-home/", home, name="system-home"),
    path("api/status/", status_check, name="api-status"),
    path("api/meta/", metadata_overview, name="api-metadata"),
    path("api/overview/", dashboard_overview, name="dashboard-overview"),
    path("api/dashboard/", agent_dashboard, name="agent-dashboard"),
    path("api/version/", version_info, name="api-version"),

    # 🔐 Secure Views
    path("secure-area/", secure_view, name="secure-area"),
    path("secure-dashboard/", SecureDashboardView.as_view(), name="secure-dashboard"),
    path("api/secure-dashboard/", SecureDashboardAPI.as_view(), name="secure-dashboard-api"),

    # 🔐 Custom Admin Site
    path("admin/", custom_admin_site.urls),

    # 📊 Admin Dashboard (template-based)
    path(
        "admin/dashboard/",
        TemplateView.as_view(template_name="admin/dashboard.html"),
        name="admin-dashboard",
    ),

    # 🔑 JWT Authentication
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # 👤 User Management
    path("api/v1/users/", include("users.urls")),
    path("", include("users.urls", namespace="users")),

    # 🛒 Marketplace APIs
    path("api/v1/marketplace/", include("marketplace.urls")),

    # 💼 Wallet & Transaction APIs
    path("api/v1/", include(router.urls)),

    # 🧪 Development / Mock Endpoint
    path("api/v1/mock-wallet/", mock_wallet_sample, name="mock-wallet"),

    # 📘 Swagger & Redoc (Admin-only)
    path("swagger.json", admin_schema_view.without_ui(cache_timeout=0), name="schema-json"),
    path("swagger.yaml", admin_schema_view.without_ui(cache_timeout=0), name="schema-yaml"),
    path("swagger/", admin_schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
    path("redoc/", admin_schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),

    # 📚 Public Swagger Docs (User Auth)
    path("docs.json", user_auth_schema_view.without_ui(cache_timeout=0), name="user-schema-json"),
    path("docs.yaml", user_auth_schema_view.without_ui(cache_timeout=0), name="user-schema-yaml"),
    path("docs/", user_auth_schema_view.with_ui("swagger", cache_timeout=0), name="user-auth-swagger-ui"),

    # 💳 Monnify Webhook Endpoint
    path("webhook/monnify/", monnify_webhook, name="monnify_webhook"),
]

# 🖼️ Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)