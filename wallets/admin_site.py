# wallets/admin_site.py

from datetime import datetime, timedelta
import csv

from django.contrib import admin
from django.db.models import Sum
from django.db.models.functions import TruncDate
from django.shortcuts import render
from django.urls import path
from django.utils import timezone
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from django.http import HttpResponse

from .admin import WalletAdmin, TransactionAdmin
from .models import Wallet, Transaction


class CustomAdminSite(admin.AdminSite):
    site_header = "Wallet Management"
    site_title = "Wallet Admin"
    index_title = "Dashboard"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("dashboard/", self.admin_view(self.dashboard_view), name="dashboard"),
            path("dashboard/export-csv/", self.admin_view(self.export_dashboard_csv), name="dashboard_export_csv"),  # ✅ CSV export
        ]
        return custom_urls + urls

    @cache_page(60 * 5)
    def dashboard_view(self, request):
        range_value = request.GET.get("range", "7")

        try:
            if range_value == "custom":
                start_dt = datetime.fromisoformat(request.GET["start_date"])
                end_dt = datetime.fromisoformat(request.GET["end_date"])
                start_date = timezone.make_aware(datetime.combine(start_dt, datetime.min.time()))
                end_date = timezone.make_aware(datetime.combine(end_dt, datetime.max.time()))
            else:
                days = int(range_value)
                end_date = timezone.now()
                start_date = end_date - timedelta(days=days)
        except Exception:
            end_date = timezone.now()
            start_date = end_date - timedelta(days=7)

        cached_metrics = cache.get('wallet_dashboard_metrics')
        if not cached_metrics:
            total_wallets = Wallet.objects.count()
            total_balance = Wallet.objects.aggregate(total=Sum("balance"))["total"] or 0
            cached_metrics = {
                "total_wallets": total_wallets,
                "total_balance": total_balance,
            }
            cache.set("wallet_dashboard_metrics", cached_metrics, timeout=300)

        tx_qs = Transaction.objects.filter(timestamp__range=(start_date, end_date))
        range_count = tx_qs.count()
        range_volume = tx_qs.aggregate(total=Sum("amount"))["total"] or 0

        today = timezone.now().date()
        tx_today = Transaction.objects.filter(timestamp__date=today)
        today_count = tx_today.count()
        today_volume = tx_today.aggregate(total=Sum("amount"))["total"] or 0

        chart_qs = (
            Transaction.objects
            .filter(timestamp__date__range=(start_date.date(), end_date.date()))
            .annotate(day=TruncDate('timestamp'))
            .values('day')
            .annotate(total=Sum('amount'))
            .order_by('day')
        )
        chart_data = {
            row['day'].isoformat(): float(row['total']) if row['total'] else 0
            for row in chart_qs
        }

        context = {
            **self.each_context(request),
            "total_wallets": cached_metrics["total_wallets"],
            "total_balance": cached_metrics["total_balance"],
            "range_days": range_value,
            "start_date": start_date.date(),
            "end_date": end_date.date(),
            "range_count": range_count,
            "range_volume": range_volume,
            "today_count": today_count,
            "today_volume": today_volume,
            "chart_data": chart_data,
        }

        return render(request, "admin/wallet_dashboard.html", context)

    def export_dashboard_csv(self, request):
        range_value = request.GET.get("range", "7")
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="dashboard_summary.csv"'

        writer = csv.writer(response)
        writer.writerow([
            "Range", "Start Date", "End Date", "Total Wallets", "Total Balance",
            "Tx Count", "Tx Volume", "Today Count", "Today Volume"
        ])

        try:
            if range_value == "custom":
                start_dt = datetime.fromisoformat(request.GET["start_date"])
                end_dt = datetime.fromisoformat(request.GET["end_date"])
                start_date = timezone.make_aware(datetime.combine(start_dt, datetime.min.time()))
                end_date = timezone.make_aware(datetime.combine(end_dt, datetime.max.time()))
            else:
                days = int(range_value)
                end_date = timezone.now()
                start_date = end_date - timedelta(days=days)
        except Exception:
            end_date = timezone.now()
            start_date = end_date - timedelta(days=7)

        tx_qs = Transaction.objects.filter(timestamp__range=(start_date, end_date))
        range_count = tx_qs.count()
        range_volume = tx_qs.aggregate(total=Sum("amount"))["total"] or 0

        today = timezone.now().date()
        tx_today = Transaction.objects.filter(timestamp__date=today)
        today_count = tx_today.count()
        today_volume = tx_today.aggregate(total=Sum("amount"))["total"] or 0

        total_wallets = Wallet.objects.count()
        total_balance = Wallet.objects.aggregate(total=Sum("balance"))["total"] or 0

        writer.writerow([
            range_value,
            start_date.date(),
            end_date.date(),
            total_wallets,
            total_balance,
            range_count,
            range_volume,
            today_count,
            today_volume
        ])
        return response


custom_admin_site = CustomAdminSite(name="custom_admin")
custom_admin_site.register(Wallet, WalletAdmin)
custom_admin_site.register(Transaction, TransactionAdmin)