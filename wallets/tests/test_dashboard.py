from django.test import TestCase, RequestFactory
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from wallets.admin_site import CustomAdminSite
from wallets.models import Wallet, Transaction
from django.utils import timezone
from datetime import timedelta
import csv
import io

User = get_user_model()

class DashboardTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='musa', password='pass')
        self.admin = User.objects.create_superuser(username='admin', email='admin@example.com', password='pass')

        # Assign Finance group
        finance_group, _ = Group.objects.get_or_create(name='Finance')
        self.user.groups.add(finance_group)

        # Create Wallet & Transactions
        self.wallet = Wallet.objects.create(owner=self.user, balance=5000)
        for i in range(3):
            Transaction.objects.create(wallet=self.wallet, amount=100 * (i + 1), timestamp=timezone.now() - timedelta(days=i))

        self.site = CustomAdminSite(name='custom_admin')

    def test_dashboard_response(self):
        request = self.factory.get('/admin/dashboard/')
        request.user = self.user
        response = self.site.dashboard_view(request)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Wallet Management Dashboard', response.content)

    def test_chart_data_present(self):
        request = self.factory.get('/admin/dashboard/')
        request.user = self.user
        response = self.site.dashboard_view(request)
        self.assertIn(b'chart_data', response.content)

    def test_metrics_are_cached(self):
        from django.core.cache import cache
        cache.delete('wallet_dashboard_metrics')
        request = self.factory.get('/admin/dashboard/')
        request.user = self.user
        self.site.dashboard_view(request)
        cached = cache.get('wallet_dashboard_metrics')
        self.assertIsNotNone(cached)
        self.assertGreaterEqual(cached['total_wallets'], 1)

    def test_csv_export_contains_correct_data(self):
        request = self.factory.get('/admin/dashboard/export-csv/?range=7')
        request.user = self.user
        response = self.site.export_dashboard_csv(request)
        self.assertEqual(response.status_code, 200)
        self.assertIn('attachment; filename="dashboard_summary.csv"', response.headers['Content-Disposition'])

        # Parse CSV content
        content = response.content.decode('utf-8')
        reader = csv.reader(io.StringIO(content))
        rows = list(reader)
        self.assertEqual(len(rows), 2)  # Header + 1 data row
        self.assertEqual(rows[0], ['Range', 'Start Date', 'End Date', 'Total Wallets', 'Total Balance',
                                   'Tx Count', 'Tx Volume', 'Today Count', 'Today Volume'])

    def test_role_based_flags(self):
        request = self.factory.get('/admin/dashboard/')
        request.user = self.admin
        response = self.site.dashboard_view(request)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Admin View', response.content)