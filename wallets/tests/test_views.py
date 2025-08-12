# wallets/tests/test_views.py

import threading
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from wallets.models import Wallet, Transaction

User = get_user_model()


class WalletTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='user', password='pass')
        self.client.login(username='user', password='pass')
        self.wallet = Wallet.objects.create(user=self.user, balance=Decimal('100.00'))
        # ✅ update for new endpoint
        self.wallet_url    = '/api/wallet/me/'
        self.top_up_url    = '/api/wallet/top-up/'
        self.withdraw_url  = '/api/wallet/withdraw/'

    def test_retrieve_wallet(self):
        resp = self.client.get(self.wallet_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(Decimal(resp.data['balance']), Decimal('100.00'))

    def test_wallet_top_up(self):
        resp = self.client.post(self.top_up_url, {'amount': '50.00'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal('150.00'))

    def test_wallet_withdraw_success(self):
        resp = self.client.post(self.withdraw_url, {'amount': '30.00'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal('70.00'))

    def test_wallet_withdraw_insufficient(self):
        resp = self.client.post(self.withdraw_url, {'amount': '200.00'})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Insufficient funds', resp.data['detail'])


class TransactionTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='user2', password='pass')
        self.client.login(username='user2', password='pass')
        self.wallet = Wallet.objects.create(user=self.user, balance=Decimal('0.00'))

        Transaction.objects.create(
            wallet=self.wallet,
            transaction_type=Transaction.Type.TOP_UP,
            amount=Decimal('100.00'),
            description='Initial deposit'
        )
        Transaction.objects.create(
            wallet=self.wallet,
            transaction_type=Transaction.Type.WITHDRAW,
            amount=Decimal('40.00'),
            description='Purchase'
        )

        self.list_url = '/api/transactions/'

    def test_list_transactions(self):
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 2)
        first = resp.data[0]
        self.assertEqual(first['transaction_type'], Transaction.Type.WITHDRAW)

    def test_list_transactions_with_type_filter(self):
        resp = self.client.get(self.list_url, {'transaction_type': Transaction.Type.TOP_UP})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]['transaction_type'], Transaction.Type.TOP_UP)

    def test_list_transactions_with_limit(self):
        resp = self.client.get(self.list_url, {'limit': 1})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)

    def test_retrieve_transaction_detail(self):
        txn = Transaction.objects.filter(wallet=self.wallet).first()
        detail_url = f'/api/transactions/{txn.id}/'
        resp = self.client.get(detail_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['id'], txn.id)


class SwaggerPermissionTests(APITestCase):
    def setUp(self):
        self.regular = User.objects.create_user(username='regular', password='pass')
        self.staff   = User.objects.create_user(username='admin',   password='pass', is_staff=True)

    def test_swagger_access_non_staff(self):
        self.client.login(username='regular', password='pass')
        resp = self.client.get('/swagger/')
        self.assertIn(resp.status_code, (status.HTTP_302_FOUND, status.HTTP_403_FORBIDDEN))

    def test_swagger_access_staff(self):
        self.client.login(username='admin', password='pass')
        resp = self.client.get('/swagger/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


class ConcurrencyTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='user3', password='pass')
        self.client.login(username='user3', password='pass')
        self.wallet = Wallet.objects.create(user=self.user, balance=Decimal('0.00'))
        self.top_up_url = '/api/wallet/top-up/'

    def test_concurrent_top_ups(self):
        def do_top_up(amount):
            self.client.post(self.top_up_url, {'amount': str(amount)})

        t1 = threading.Thread(target=do_top_up, args=(50,))
        t2 = threading.Thread(target=do_top_up, args=(70,))
        t1.start(); t2.start()
        t1.join();  t2.join()

        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal('120.00'))


class SanityCheck(TestCase):
    def test_debug(self):
        print("✅ Tests are being discovered")
        self.assertEqual(2 + 2, 4)