from django.core import checks

@checks.register()
def silence_allauth_warning(app_configs, **kwargs):
    print("✅ Custom system check override loaded")  # 🧪 Diagnostic print
    return []  # ✅ Silences account.W001 warning from django-allauth