from django.core.cache import cache
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Wallet, Transaction

@receiver([post_save, post_delete], sender=Wallet)
@receiver([post_save, post_delete], sender=Transaction)
def invalidate_dashboard_cache(sender, **kwargs):
    cache.delete('wallet_dashboard_metrics')