import csv
from django.contrib import admin
from django.http import HttpResponse
from django.urls import path

from .models import Wallet, Transaction
from .views import export_dashboard_pdf


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance', 'created_at', 'updated_at')
    search_fields = ('user__username',)
    list_filter = ('created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    list_select_related = ('user',)
    change_list_template = "admin/wallets/wallet_change_list.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'export-report/',
                self.admin_site.admin_view(export_dashboard_pdf),
                name='wallet-export-report'
            ),
        ]
        return custom_urls + urls


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('wallet', 'transaction_type', 'amount', 'bundle', 'timestamp')
    search_fields = ('wallet__user__username', 'bundle__name', 'description')
    list_filter = ('transaction_type', 'timestamp')
    list_per_page = 25
    date_hierarchy = 'timestamp'
    ordering = ('-timestamp',)
    readonly_fields = ('timestamp',)
    list_select_related = ('wallet', 'bundle')
    raw_id_fields = ('wallet', 'bundle')  # ✅ Stable reference for migrations
    actions = ('export_csv', 'flag_suspicious')

    def export_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=transactions.csv'
        writer = csv.writer(response)
        writer.writerow(['ID', 'User', 'Type', 'Amount', 'Timestamp'])
        for tx in queryset:
            writer.writerow([
                tx.id,
                tx.wallet.user.username,
                tx.transaction_type,
                tx.amount,
                tx.timestamp,
            ])
        return response
    export_csv.short_description = "Export selected transactions to CSV"

    def flag_suspicious(self, request, queryset):
        updated = queryset.update(is_flagged=True)
        self.message_user(request, f"{updated} transactions flagged as suspicious.")
    flag_suspicious.short_description = "Flag selected transactions as suspicious"