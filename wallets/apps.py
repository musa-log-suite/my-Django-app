# wallets/apps.py

from django.apps import AppConfig


class WalletsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'  # ✅ corrected spelling
    name = 'wallets'

    def ready(self):
        # 🔄 Hook signal handlers to enable cache invalidation & other startup tasks
        import wallets.signals  # ✅ activates smart cache invalidation on model changes