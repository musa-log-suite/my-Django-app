from django.contrib import admin
from .models import Product, Purchase


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "provider", "product_type", "value", "price", "active", "popular", "updated_at")
    list_filter = ("provider", "product_type", "active", "popular")
    search_fields = ("name", "code", "description")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("provider", "product_type", "value")

    fieldsets = (
        (None, {
            "fields": (
                "name",
                "code",
                "product_type",
                "provider",
                "category",
                "value",
                "price",
                "description",
                "active",
                "popular",
                "created_at",
                "updated_at"
            )
        }),
    )


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ("user", "product", "amount", "status", "timestamp")
    list_filter = ("status", "product__provider", "product__product_type")
    search_fields = ("user__email", "product__name")
    readonly_fields = ("amount", "timestamp")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user", "product")