from rest_framework import serializers
from wallets.models import Transaction
from marketplace.models import Product, Purchase, Category


class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer for Category model.
    Exposes ID and name fields.
    """
    class Meta:
        model = Category
        fields = ['id', 'name']


class ProductSerializer(serializers.ModelSerializer):
    """
    Serializer for Product model.
    Exposes all fields, including availability and timestamps.
    """
    category = CategorySerializer(read_only=True)  # Optional nested display

    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = [
            'id',
            'active',
            'created_at',
            'updated_at',
        ]


class BuyBundleSerializer(serializers.Serializer):
    """
    Validates a bundle purchase and debits the user's wallet.
    Creates a Transaction record.
    """
    bundle_id = serializers.IntegerField(write_only=True)
    description = serializers.CharField(required=False, allow_blank=True)

    def validate_bundle_id(self, value):
        try:
            product = Product.objects.get(id=value, active=True)
        except Product.DoesNotExist:
            raise serializers.ValidationError("Bundle not found.")
        return product

    def create(self, validated_data):
        user = self.context['request'].user
        wallet = getattr(user, 'wallet', None)
        bundle = validated_data['bundle_id']
        description = validated_data.get('description', f"Purchased {bundle.name}")

        if wallet is None:
            raise serializers.ValidationError("No wallet found for user.")
        if wallet.balance < bundle.price:
            raise serializers.ValidationError("Insufficient wallet balance.")

        wallet.balance -= bundle.price
        wallet.save()

        return Transaction.objects.create(
            wallet=wallet,
            transaction_type=Transaction.Type.PURCHASE,
            amount=bundle.price,
            bundle=bundle,
            description=description
        )


class PurchaseSerializer(serializers.ModelSerializer):
    """
    Serializer for Purchase model.
    Automatically sets amount from the product price.
    """
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    timestamp = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Purchase
        fields = [
            'id',
            'product',
            'amount',
            'timestamp',
        ]
        read_only_fields = [
            'id',
            'amount',
            'timestamp',
        ]

    def validate(self, attrs):
        product = attrs.get('product')
        attrs['amount'] = product.price
        return attrs

    def create(self, validated_data):
        user = self.context['request'].user
        purchase = Purchase(user=user, **validated_data)
        purchase.save()
        return purchase