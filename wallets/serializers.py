# wallets/serializers.py

from rest_framework import serializers
from .models import Wallet, Transaction


class TopUpSerializer(serializers.Serializer):
    """
    Validates wallet top-up input. Requires amount ≥ ₦0.01.
    """
    amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=0.01,
        error_messages={
            'required': 'Amount is required to top-up.',
            'min_value': 'Minimum top-up is ₦0.01.',
        }
    )


class WithdrawSerializer(serializers.Serializer):
    """
    Validates wallet withdrawal input. Requires amount ≥ ₦0.01.
    """
    amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=0.01,
        error_messages={
            'required': 'Amount is required to withdraw.',
            'min_value': 'Minimum withdrawal is ₦0.01.',
        }
    )


class TransactionSerializer(serializers.ModelSerializer):
    """
    Serializer for Transaction model.
    Displays transaction type, amount, bundle, description, and timestamp.
    """
    bundle = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Transaction
        fields = [
            'id',
            'transaction_type',
            'amount',
            'bundle',
            'description',
            'timestamp',
        ]
        read_only_fields = ['id', 'timestamp']


class WalletSerializer(serializers.ModelSerializer):
    """
    Serializer for Wallet model.
    Displays user info, virtual account details, balance,
    timestamps, and optional transaction history.
    """
    user = serializers.StringRelatedField(read_only=True)
    account_number = serializers.CharField(read_only=True)
    bank_name = serializers.CharField(read_only=True)
    history = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Wallet
        fields = [
            'id',
            'user',
            'account_number',
            'bank_name',
            'balance',
            'created_at',
            'updated_at',
            'history',
        ]
        read_only_fields = [
            'id',
            'user',
            'account_number',
            'bank_name',
            'balance',
            'created_at',
            'updated_at',
        ]

    def get_history(self, wallet):
        """
        Returns the wallet’s latest transactions,
        sorted newest first. Supports ?limit=N.
        """
        qs = wallet.transactions.select_related('bundle').order_by('-timestamp')
        request = self.context.get('request')
        if request:
            limit = request.query_params.get('limit')
            if limit and limit.isdigit():
                qs = qs[:int(limit)]
        return TransactionSerializer(qs, many=True, context=self.context).data