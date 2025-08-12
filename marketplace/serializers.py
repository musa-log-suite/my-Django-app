from decimal import Decimal
from rest_framework import serializers
from .models import Product, Purchase


class ProductSerializer(serializers.ModelSerializer):
    """
    Serializer for Product model.
    Exposes core fields, vendor metadata, and status indicators.
    """
    provider_display = serializers.CharField(source='get_provider_display', read_only=True)
    product_type_display = serializers.CharField(source='get_product_type_display', read_only=True)

    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'code',
            'product_type',
            'product_type_display',
            'provider',
            'provider_display',
            'value',
            'price',
            'description',
            'active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'active',
            'created_at',
            'updated_at',
            'product_type_display',
            'provider_display',
        ]


class PurchaseSerializer(serializers.ModelSerializer):
    """
    Serializer for Purchase model.
    Automatically pulls product price, attaches request user,
    and exposes status/timestamp metadata.
    """
    amount = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        read_only=True,
        min_value=Decimal("0.00")  # ✅ Fix: use Decimal type
    )
    timestamp = serializers.DateTimeField(read_only=True)
    status = serializers.CharField(read_only=True)

    class Meta:
        model = Purchase
        fields = [
            'id',
            'product',
            'amount',
            'status',
            'timestamp',
        ]
        read_only_fields = [
            'id',
            'amount',
            'status',
            'timestamp',
        ]

    def validate(self, attrs):
        product = attrs.get('product')
        if not product.active:
            raise serializers.ValidationError("Product is not available for purchase.")
        attrs['amount'] = product.price
        return attrs

    def create(self, validated_data):
        user = self.context['request'].user
        purchase = Purchase(user=user, **validated_data)
        purchase.save()  # Triggers atomic wallet debit + transaction log
        return purchase


class ProviderSerializer(serializers.Serializer):
    """
    Simple serializer to display provider info.
    """
    id = serializers.CharField()
    name = serializers.CharField()


class CategorySerializer(serializers.Serializer):
    """
    Serializer to format product_type entries.
    """
    id = serializers.CharField()
    label = serializers.CharField()


class PopularProductSerializer(serializers.ModelSerializer):
    """
    Serializer for popular products with ranking logic.
    """
    purchase_count = serializers.IntegerField(read_only=True)
    provider_display = serializers.CharField(source='get_provider_display', read_only=True)
    product_type_display = serializers.CharField(source='get_product_type_display', read_only=True)

    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'provider',
            'provider_display',
            'product_type',
            'product_type_display',
            'value',
            'price',
            'purchase_count',
        ]
        read_only_fields = fields