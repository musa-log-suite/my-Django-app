import json
import hmac
import hashlib
from decimal import Decimal

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.templatetags.static import static
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination

from django_filters.rest_framework import DjangoFilterBackend, FilterSet, DateFromToRangeFilter
from drf_yasg.utils import swagger_auto_schema

from .models import Wallet, Transaction
from .serializers import (
    WalletSerializer,
    TransactionSerializer,
    TopUpSerializer,
    WithdrawSerializer,
)

# -------------------------------------------------------------------
# TransactionFilter for DjangoFilterBackend
# -------------------------------------------------------------------
class TransactionFilter(FilterSet):
    timestamp = DateFromToRangeFilter(field_name='timestamp')

    class Meta:
        model = Transaction
        fields = {
            'transaction_type': ['exact'],
            'timestamp': ['exact', 'gte', 'lte'],
        }

# -------------------------------------------------------------------
# WalletViewSet: View & mutate the authenticated user’s wallet
# -------------------------------------------------------------------
class WalletViewSet(viewsets.GenericViewSet):
    """
    me:
      GET /wallet/me/         → get current user’s wallet
    top_up:
      POST /wallet/top-up/    → deposit funds
    withdraw:
      POST /wallet/withdraw/  → withdraw funds
    """
    serializer_class = WalletSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return get_object_or_404(Wallet, user=self.request.user)

    @swagger_auto_schema(
        operation_description="Retrieve the authenticated user's wallet.",
        responses={200: WalletSerializer},
        tags=["Wallet Operations"],
    )
    @action(detail=False, methods=['get'], url_path='me')
    def me(self, request):
        wallet = self.get_object()
        serializer = self.get_serializer(wallet, context={'request': request})
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Deposit funds into the authenticated user's wallet.",
        request_body=TopUpSerializer,
        responses={200: WalletSerializer},
        tags=["Wallet Operations"],
    )
    @action(detail=False, methods=['post'], url_path='top-up')
    @transaction.atomic
    def top_up(self, request):
        wallet = Wallet.objects.select_for_update().get(user=request.user)
        ser = TopUpSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        amount = ser.validated_data['amount']

        wallet.balance += amount
        wallet.save()

        Transaction.objects.create(
            wallet=wallet,
            transaction_type=Transaction.TOPUP,
            amount=amount,
            description='Wallet top-up'
        )

        out = WalletSerializer(wallet, context={'request': request})
        return Response(out.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Withdraw funds from the authenticated user's wallet.",
        request_body=WithdrawSerializer,
        responses={200: WalletSerializer, 400: "Insufficient funds."},
        tags=["Wallet Operations"],
    )
    @action(detail=False, methods=['post'], url_path='withdraw')
    @transaction.atomic
    def withdraw(self, request):
        wallet = Wallet.objects.select_for_update().get(user=request.user)
        ser = WithdrawSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        amount = ser.validated_data['amount']

        if wallet.balance < amount:
            return Response(
                {"detail": "Insufficient funds."},
                status=status.HTTP_400_BAD_REQUEST
            )

        wallet.balance -= amount
        wallet.save()

        Transaction.objects.create(
            wallet=wallet,
            transaction_type=Transaction.WITHDRAW,
            amount=amount,
            description='Wallet withdrawal'
        )

        out = WalletSerializer(wallet, context={'request': request})
        return Response(out.data, status=status.HTTP_200_OK)

# -------------------------------------------------------------------
# TransactionViewSet: Read-only listing & detail of user’s transactions
# -------------------------------------------------------------------
class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list:
      GET /transactions/      → list, filter, search, paginate
    retrieve:
      GET /transactions/{id}/ → detail
    """
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = LimitOffsetPagination
    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    )
    filterset_class = TransactionFilter
    search_fields = ('description',)
    ordering_fields = ('timestamp', 'amount')
    ordering = ('-timestamp',)

    def get_queryset(self):
        wallet = get_object_or_404(Wallet, user=self.request.user)
        return wallet.transactions.select_related('bundle')

    @swagger_auto_schema(
        operation_description="List wallet transactions.",
        responses={200: TransactionSerializer(many=True)},
        tags=["Transaction History"],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Retrieve a single transaction by ID.",
        responses={200: TransactionSerializer},
        tags=["Transaction History"],
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

# -------------------------------------------------------------------
# Monnify Webhook: Automatically credit wallet on successful transfer
# -------------------------------------------------------------------
@csrf_exempt
def monnify_webhook(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'invalid method'}, status=405)

    signature = request.headers.get('monnify-signature')
    computed_signature = hmac.new(
        key=bytes(settings.MONNIFY_SECRET_KEY, 'utf-8'),
        msg=request.body,
        digestmod=hashlib.sha512
    ).hexdigest()

    if signature != computed_signature:
        return JsonResponse({'status': 'unauthorized'}, status=401)

    payload = json.loads(request.body)
    event_type = payload.get('eventType')
    payment_info = payload.get('eventData', {})

    if event_type == 'SUCCESSFUL_TRANSACTION':
        account_number = payment_info.get('accountDetails', {}).get('accountNumber')
        amount = Decimal(payment_info.get('amount', 0))

        try:
            wallet = Wallet.objects.get(account_number=account_number)
            wallet.balance += amount
            wallet.save(update_fields=['balance'])

            Transaction.objects.create(
                wallet=wallet,
                transaction_type=Transaction.TOPUP,
                amount=amount,
                description='Monnify webhook credit'
            )

            return JsonResponse({'status': 'wallet credited'}, status=200)
        except Wallet.DoesNotExist:
            return JsonResponse({'status': 'wallet not found'}, status=404)

    return JsonResponse({'status': 'ignored'}, status=200)

# -------------------------------------------------------------------
# PDF Export View
# -------------------------------------------------------------------
def export_dashboard_pdf(request):
    """
    Render the wallet dashboard as a PDF.
    """
    context = {
        'start_date': '2024-01-01',
        'end_date': '2024-04-24',
        'total_wallets': 50,
        'total_balance': 25000,
        'range_count': 120,
        'range_volume': 18000,
        'today_count': 5,
        'today_volume': 700,
        'chart_url': request.build_absolute_uri(static('chart.png')),
        'now': timezone.now(),
    }

    html_string = render_to_string('dashboard_pdf.html', context)
    html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
    pdf_file = html.write_pdf()

    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=wallet_report.pdf'
    return response