from django.http import HttpResponse, JsonResponse
from django.utils.timezone import now
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.shortcuts import render

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from wallets.models import Wallet
from marketplace.models import Product, Purchase

# 🏠 Home Endpoint
def home(request):
    return HttpResponse("<h2>👋 Welcome to Musa's Django API</h2>")

# 📶 API Status Check
@swagger_auto_schema(
    method='get',
    operation_summary="API Status Check",
    operation_description="Returns a success message if the API is live and responsive.",
    responses={200: openapi.Response(description="API is online")}
)
@api_view(['GET'])
@permission_classes([AllowAny])
def status_check(request):
    return JsonResponse({"status": "ok", "message": "API is live 🚀"})

# 📘 Metadata Overview
@swagger_auto_schema(
    method='get',
    operation_summary="Metadata Overview",
    operation_description="Displays project name, developer, version, and available modules.",
    responses={200: openapi.Response(
        description="Project metadata",
        examples={
            "application/json": {
                "name": "Musa API",
                "version": "v1",
                "developer": "Musa",
                "features": ["Wallet", "Marketplace", "OTP Verification"]
            }
        }
    )}
)
@api_view(['GET'])
@permission_classes([AllowAny])
def metadata_overview(request):
    data = {
        "name": "Musa API",
        "version": "v1",
        "developer": "Musa",
        "features": ["Wallet", "Marketplace", "OTP Verification"]
    }
    return JsonResponse(data)

# 📊 Dashboard Overview
@swagger_auto_schema(
    method='get',
    operation_summary="Dashboard Overview",
    operation_description="Shows current totals for users, wallets, purchases, and products.",
    responses={200: openapi.Response(
        description="System dashboard stats",
        examples={
            "application/json": {
                "users": 25,
                "wallets": 18,
                "products": 42,
                "purchases": 77,
                "server_time": "2025-08-04T21:36:00Z"
            }
        }
    )}
)
@api_view(['GET'])
@permission_classes([AllowAny])
def dashboard_overview(request):
    data = {
        "users": get_user_model().objects.count(),
        "wallets": Wallet.objects.count(),
        "products": Product.objects.count(),
        "purchases": Purchase.objects.count(),
        "server_time": now()
    }
    return JsonResponse(data)

# 🧮 Agent Dashboard Data (for React Frontend)
@swagger_auto_schema(
    method='get',
    operation_summary="Agent Dashboard",
    operation_description="Provides wallet balance and commission earned for frontend display.",
    responses={200: openapi.Response(
        description="Wallet and commission totals",
        examples={
            "application/json": {
                "wallet_balance": 12500,
                "commission_earned": 3000
            }
        }
    )}
)
@api_view(['GET'])
@permission_classes([AllowAny])
def agent_dashboard(request):
    data = {
        "wallet_balance": 12500,
        "commission_earned": 3000
    }
    return JsonResponse(data)

# 🔖 API Version Info
@swagger_auto_schema(
    method='get',
    operation_summary="API Version Info",
    operation_description="Returns the current version, release date, and stability status.",
    responses={200: openapi.Response(
        description="Version metadata",
        examples={
            "application/json": {
                "version": "v1",
                "release_date": "2025-08-04",
                "status": "stable"
            }
        }
    )}
)
@api_view(['GET'])
@permission_classes([AllowAny])
def version_info(request):
    return JsonResponse({
        "version": "v1",
        "release_date": "2025-08-04",
        "status": "stable"
    })

# 🔐 Secure Function-Based View
@login_required
def secure_view(request):
    return render(request, "secure/area.html")

# 🔐 Secure Class-Based Dashboard View with Stats
@method_decorator(login_required, name='dispatch')
class SecureDashboardView(TemplateView):
    template_name = "secure/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        context["total_purchases"] = Purchase.objects.filter(user=user).count()
        context["recent_purchases"] = Purchase.objects.filter(user=user).order_by("-created_at")[:5]

        wallet = Wallet.objects.filter(user=user).first()
        context["wallet_balance"] = wallet.balance if wallet else 0

        return context

# 🔐 Secure Dashboard API (for frontend)
class SecureDashboardAPI(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Secure Dashboard API",
        operation_description="Returns wallet balance, total purchases, and recent purchase history for the authenticated user.",
        responses={200: openapi.Response(
            description="User dashboard data",
            examples={
                "application/json": {
                    "wallet_balance": 8500,
                    "total_purchases": 12,
                    "recent_purchases": [
                        {"product": "Solar Lamp", "amount": 2500, "date": "2025-08-08"},
                        {"product": "Phone Charger", "amount": 1500, "date": "2025-08-07"}
                    ]
                }
            }
        )}
    )
    def get(self, request):
        user = request.user
        wallet = Wallet.objects.filter(user=user).first()
        purchases = Purchase.objects.filter(user=user).order_by("-created_at")[:5]

        data = {
            "wallet_balance": wallet.balance if wallet else 0,
            "total_purchases": Purchase.objects.filter(user=user).count(),
            "recent_purchases": [
                {
                    "product": p.product.name,
                    "amount": p.amount,
                    "date": p.created_at.strftime("%Y-%m-%d")
                } for p in purchases
            ]
        }
        return Response(data)