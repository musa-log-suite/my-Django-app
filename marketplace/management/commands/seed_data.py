from django.core.management.base import BaseCommand
from marketplace.models import Product

class Command(BaseCommand):
    help = "Seed the database with default airtime/data bundles"

    def handle(self, *args, **options):
        bundles = [
            {
                "name": "MTN ₦500 Airtime",
                "code": "MTN500AIR",
                "product_type": Product.AIRTIME,
                "provider": Product.MTN,
                "value": 500,
                "price": 490,
                "description": "Recharge ₦500 MTN airtime"
            },
            {
                "name": "Airtel ₦1000 Data",
                "code": "AIRTEL1GB",
                "product_type": Product.DATA,
                "provider": Product.AIRTEL,
                "value": 1024,  # in MB
                "price": 950,
                "description": "1GB Airtel data plan"
            },
            {
                "name": "Glo ₦2000 Data",
                "code": "GLO2_5GB",
                "product_type": Product.DATA,
                "provider": Product.GLO,
                "value": 2560,
                "price": 1900,
                "description": "2.5GB Glo data package"
            },
        ]

        for bundle in bundles:
            Product.objects.update_or_create(
                name=bundle["name"],
                defaults=bundle,
            )

        self.stdout.write(self.style.SUCCESS("✅ Seeded default bundles successfully"))