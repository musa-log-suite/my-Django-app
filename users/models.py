from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser, PermissionsMixin, BaseUserManager
)
from django.utils import timezone
from django.core.validators import RegexValidator


def default_expiry():
    return timezone.now() + timezone.timedelta(minutes=5)


class UserManager(BaseUserManager):
    def create_user(self, phone_number, password=None, **extra_fields):
        if not phone_number:
            raise ValueError("Phone number must be set")
        extra_fields.setdefault('is_active', False)  # Inactive until OTP verification
        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if not extra_fields.get('is_staff'):
            raise ValueError("Superuser must have is_staff=True.")
        if not extra_fields.get('is_superuser'):
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(phone_number, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    phone_regex = RegexValidator(
        regex=r'^\+?\d{9,15}$',
        message="Phone number must be entered in the format: '+2348000000000'. Up to 15 digits allowed."
    )
    phone_number = models.CharField(
        max_length=15,
        unique=True,
        validators=[phone_regex],
        verbose_name="Phone Number"
    )
    email = models.EmailField(
        unique=True,
        null=True,
        blank=True,
        verbose_name="Email Address"
    )
    full_name = models.CharField(
        max_length=120,
        blank=True,
        null=True,
        verbose_name="Full Name"
    )

    # 🎯 Feature flags
    is_agent = models.BooleanField(default=False, verbose_name="Agent Status")
    is_phone_verified = models.BooleanField(default=False, verbose_name="Phone Verified")

    # ✅ Account status
    is_active = models.BooleanField(default=False, verbose_name="Active")
    is_staff = models.BooleanField(default=False, verbose_name="Staff")

    # 📅 Metadata
    date_joined = models.DateTimeField(default=timezone.now, verbose_name="Date Joined")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Last Updated")

    objects = UserManager()

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return self.phone_number

    def get_full_name(self):
        return self.full_name or self.phone_number

    def get_short_name(self):
        return self.phone_number

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ['-date_joined']


class OTP(models.Model):
    """
    One-Time Password model for verifying users during signup/login flows.
    """
    PURPOSE_CHOICES = [
        ('signup', 'Signup'),
        ('login', 'Login'),
        ('password_reset', 'Password Reset'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='otps',
        verbose_name="User"
    )
    code = models.CharField(max_length=6, verbose_name="OTP Code")
    purpose = models.CharField(
        max_length=20,
        choices=PURPOSE_CHOICES,
        verbose_name="Purpose"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    expires_at = models.DateTimeField(default=default_expiry, verbose_name="Expires At")
    is_used = models.BooleanField(default=False, verbose_name="Used")

    class Meta:
        indexes = [
            models.Index(fields=['user', 'purpose', 'is_used']),
        ]
        ordering = ['-created_at']
        verbose_name = "OTP"
        verbose_name_plural = "OTPs"

    def __str__(self):
        return f"OTP for {self.user.phone_number} — {self.code} ({self.purpose})"


class OTPAttempt(models.Model):
    """
    Tracks each OTP verification attempt for auditing and abuse prevention.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='otp_attempts',
        verbose_name="User"
    )
    code_entered = models.CharField(
        max_length=6,
        blank=True,
        default='',
        verbose_name="Code Entered"
    )
    success = models.BooleanField(default=False, verbose_name="Success")
    attempt_time = models.DateTimeField(auto_now_add=True, verbose_name="Attempt Time")

    class Meta:
        indexes = [
            models.Index(fields=['user', 'success']),
        ]
        ordering = ['-attempt_time']
        verbose_name = "OTP Attempt"
        verbose_name_plural = "OTP Attempts"

    def __str__(self):
        status = "✅ Success" if self.success else "❌ Failed"
        return f"{self.user.phone_number}@{self.attempt_time.strftime('%Y-%m-%d %H:%M:%S')} → {status}"