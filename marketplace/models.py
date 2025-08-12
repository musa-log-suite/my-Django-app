from django.conf import settings
from django.db import models, transaction as db_transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from wallets.models import Wallet, Transaction as WalletTransaction


class Category(models.Model):
    """
    Represents a product category (e.g. Data, Airtime, SMS).
    """
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    """
    Represents a digital product available for purchase,
    such as airtime or data bundles.
    """

    AIRTIME = 'airtime'
    DATA = 'data'
    PRODUCT_TYPE_CHOICES = [
        (AIRTIME, 'Airtime'),
        (DATA, 'Data Bundle'),
    ]

    MTN = 'mtn'
    GLO = 'glo'
    AIRTEL = 'airtel'
    NINE_M = '9mobile'
    PROVIDER_CHOICES = [
        (MTN, 'MTN'),
        (GLO, 'Glo'),
        (AIRTEL, 'Airtel'),
        (NINE_M, '9mobile'),
    ]

    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True, help_text="Vendor API product code")
    product_type = models.CharField(max_length=10, choices=PRODUCT_TYPE_CHOICES)
    provider = models.CharField(max_length=10, choices=PROVIDER_CHOICES)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    value = models.DecimalField(max_digits=10, decimal_places=2, help_text="E.g. 100 naira or 500 MB")
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="What agent pays per unit")
    description = models.TextField(blank=True, help_text="Optional description for this bundle")
    active = models.BooleanField(default=True, help_text="Designates if this product is available for purchase.")
    popular = models.BooleanField(default=False, help_text="Marks product as popular for homepage or trending list")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['provider', 'product_type', 'value']

    def __str__(self):
        return f"{self.get_provider_display()} {self.get_product_type_display()} {self.value}"


class Purchase(models.Model):
    """
    Logs a user's purchase of a Product.
    On save, debits the Wallet and records a WalletTransaction.
    """

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='purchases')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='purchases')
    amount = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='completed')
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user.email} → {self.product.name} ({self.amount})"

    def save(self, *args, **kwargs):
        with db_transaction.atomic():
            wallet = Wallet.objects.select_for_update().get(user=self.user)
            self.amount = self.product.price

            if wallet.balance < self.amount:
                raise ValidationError("Insufficient wallet balance for purchase.")

            wallet.balance -= self.amount
            wallet.save(update_fields=['balance'])

            super().save(*args, **kwargs)

            WalletTransaction.objects.create(
                wallet=wallet,
                transaction_type=WalletTransaction.Type.PURCHASE,
                amount=self.amount,
                bundle=self.product,
                description=f"Purchased {self.product.name}"
            )

            # 💡 Hook for commissions, referral rewards, or promo tracking can go here