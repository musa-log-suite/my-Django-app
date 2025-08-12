from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

# ✅ Import Monnify service
from services.monnify import create_virtual_account


class Wallet(models.Model):
    """
    One-to-one wallet for each user, tracks balance and virtual account info.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wallet'
    )
    account_number = models.CharField(
        max_length=10,
        unique=True,
        blank=True,
        help_text="Virtual NUBAN-style account number"
    )
    bank_name = models.CharField(
        max_length=50,
        default='Moniepoint',
        help_text="Provider or bank name"
    )
    balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} — {self.account_number} (₦{self.balance})"


class Transaction(models.Model):
    """
    Records all financial activity on a Wallet.
    """
    TOPUP = 'topup'
    WITHDRAW = 'withdraw'
    PURCHASE = 'purchase'
    TRANSACTION_TYPE_CHOICES = [
        (TOPUP, 'Top-up'),
        (WITHDRAW, 'Withdraw'),
        (PURCHASE, 'Purchase'),
    ]

    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    transaction_type = models.CharField(
        max_length=10,
        choices=TRANSACTION_TYPE_CHOICES,
        default=TOPUP,
        help_text="Type of transaction"
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )
    bundle = models.ForeignKey(
        'marketplace.Product',  # ✅ Use string path to avoid import errors during migration
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions'
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Optional transaction note"
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.wallet.user.email} — {self.transaction_type.capitalize()} ₦{self.amount}"


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_wallet_for_new_user(sender, instance, created, **kwargs):
    """
    Auto-creates a wallet with Monnify virtual account when a new user is registered.
    """
    if created:
        account_data = create_virtual_account(instance)
        Wallet.objects.create(
            user=instance,
            account_number=account_data['account_number'],
            bank_name=account_data['bank_name']
        )