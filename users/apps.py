from django.apps import AppConfig

class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'

    def ready(self):
        try:
            from . import checks         # ✅ Load custom system check override
           # from . import monkey_patch  # 🧨 Disable Allauth's W001 warning
        except ImportError:
            # Gracefully skip if files are missing (useful in early dev stages)
            pass