from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.urls import path
from django.http import HttpResponse
from django.template.response import TemplateResponse
from django.db.models import Count
import csv

from users.models import User, OTP, OTPAttempt


# ─────────────────────────────────────────────────────────────
# ✅ Custom Admin Site
# ─────────────────────────────────────────────────────────────

class CustomAdminSite(admin.AdminSite):
    site_header = "Your Platform Admin"
    site_title = "Dashboard"
    index_title = "Welcome to Your Control Panel"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("dashboard/", self.admin_view(self.dashboard_view), name="dashboard"),
        ]
        return custom_urls + urls

    def dashboard_view(self, request):
        context = dict(
            self.each_context(request),
            total_users=User.objects.count(),
            verified_users=User.objects.filter(is_phone_verified=True).count(),
            agent_count=User.objects.filter(is_agent=True).count(),
            active_users=User.objects.filter(is_active=True).count(),
            otp_issued=OTP.objects.count(),
            otp_attempts=OTPAttempt.objects.count(),

            # 🔢 Chart Metrics
            used_otps=OTP.objects.filter(is_used=True).count(),
            unused_otps=OTP.objects.filter(is_used=False).count(),
            success_attempts=OTPAttempt.objects.filter(success=True).count(),
            failed_attempts=OTPAttempt.objects.filter(success=False).count(),
        )
        return TemplateResponse(request, "admin/dashboard.html", context)


custom_admin_site = CustomAdminSite(name="custom_admin")


# ─────────────────────────────────────────────────────────────
# ✅ User Admin
# ─────────────────────────────────────────────────────────────

@admin.register(User, site=custom_admin_site)
class UserAdmin(BaseUserAdmin):
    list_display = (
        "email", "phone_number", "full_name", "is_agent", "is_phone_verified",
        "is_active", "is_staff", "date_joined"
    )
    list_filter = ("is_agent", "is_phone_verified", "is_active", "is_staff")
    search_fields = ("email", "phone_number", "full_name")
    ordering = ("-date_joined",)
    readonly_fields = ("date_joined", "updated_at", "last_login")

    fieldsets = (
        (None, {"fields": ("email", "phone_number", "password")}),
        ("Personal Info", {"fields": ("full_name",)}),
        ("Roles & Status", {
            "fields": ("is_agent", "is_phone_verified", "is_active", "is_staff", "is_superuser")
        }),
        ("Dates", {"fields": ("date_joined", "updated_at", "last_login")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "phone_number", "full_name", "password1", "password2", "is_agent"),
        }),
    )

    actions = ["verify_selected", "export_users_csv"]

    def verify_selected(self, request, queryset):
        count = queryset.update(is_phone_verified=True)
        self.message_user(request, f"{count} users have been verified.")
    verify_selected.short_description = "✅ Verify selected users"

    def export_users_csv(self, request, queryset):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="users.csv"'
        writer = csv.writer(response)
        writer.writerow(["Email", "Phone", "Full Name", "Agent", "Phone Verified", "Date Joined"])
        for user in queryset:
            writer.writerow([
                user.email, user.phone_number, user.full_name,
                user.is_agent, user.is_phone_verified, user.date_joined
            ])
        return response
    export_users_csv.short_description = "📤 Export selected users as CSV"


# ─────────────────────────────────────────────────────────────
# ✅ OTP Admin
# ─────────────────────────────────────────────────────────────

@admin.register(OTP, site=custom_admin_site)
class OTPAdmin(admin.ModelAdmin):
    list_display = ("user", "code", "purpose", "is_used", "created_at")
    list_filter = ("purpose", "is_used")
    search_fields = ("user__email", "code")
    readonly_fields = ("created_at",)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user")

    actions = ["export_otp_csv"]

    def export_otp_csv(self, request, queryset):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="otp.csv"'
        writer = csv.writer(response)
        writer.writerow(["User", "Code", "Purpose", "Used", "Created At"])
        for otp in queryset:
            writer.writerow([
                otp.user.email, otp.code, otp.purpose,
                otp.is_used, otp.created_at
            ])
        return response
    export_otp_csv.short_description = "📥 Export selected OTPs as CSV"


# ─────────────────────────────────────────────────────────────
# ✅ OTP Attempt Admin
# ─────────────────────────────────────────────────────────────

@admin.register(OTPAttempt, site=custom_admin_site)
class OTPAttemptAdmin(admin.ModelAdmin):
    list_display = ("user", "code_entered", "success", "attempt_time")
    list_filter = ("success",)
    search_fields = ("user__email", "code_entered")
    readonly_fields = ("attempt_time",)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user")

    actions = ["export_attempts_csv"]

    def export_attempts_csv(self, request, queryset):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="otp_attempts.csv"'
        writer = csv.writer(response)
        writer.writerow(["User", "Code Entered", "Success", "Attempt Time"])
        for attempt in queryset:
            writer.writerow([
                attempt.user.email, attempt.code_entered,
                attempt.success, attempt.attempt_time
            ])
        return response
    export_attempts_csv.short_description = "🗂 Export selected OTP attempts as CSV"