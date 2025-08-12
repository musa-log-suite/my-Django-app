from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()

# ─────────────────────────────────────────────────────────────
# ✅ Registration Form with OTP
# ─────────────────────────────────────────────────────────────

class UserRegisterForm(forms.ModelForm):
    full_name = forms.CharField(label="Full Name", max_length=150)
    phone_number = forms.CharField(label="Phone Number", max_length=20)
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirm Password", widget=forms.PasswordInput)
    otp = forms.CharField(label="OTP", max_length=6, widget=forms.TextInput(attrs={"placeholder": "Enter OTP"}))

    class Meta:
        model = User
        fields = ["email", "full_name", "phone_number"]

    def clean_password2(self):
        p1 = self.cleaned_data.get("password1")
        p2 = self.cleaned_data.get("password2")
        if not p1 or not p2:
            raise ValidationError("Both password fields are required.")
        if p1 != p2:
            raise ValidationError("Passwords do not match.")
        return p2

    def clean_otp(self):
        otp = self.cleaned_data.get("otp")
        if not otp or not otp.isdigit() or len(otp) != 6:
            raise ValidationError("Enter a valid 6-digit OTP.")
        # Optional: Add logic to verify OTP from backend/session
        return otp

    def save(self, commit=True):
        user = super().save(commit=False)
        user.full_name = self.cleaned_data["full_name"]
        user.phone_number = self.cleaned_data["phone_number"]
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


# ─────────────────────────────────────────────────────────────
# 🔑 Password Reset Request Form with OTP
# ─────────────────────────────────────────────────────────────

class PasswordResetRequestForm(forms.Form):
    phone_or_email = forms.CharField(
        label="Phone or Email",
        max_length=100,
        widget=forms.TextInput(attrs={"placeholder": "Enter phone or email"})
    )
    otp = forms.CharField(
        label="OTP",
        max_length=6,
        widget=forms.TextInput(attrs={"placeholder": "Enter OTP"})
    )

    def clean_phone_or_email(self):
        value = self.cleaned_data.get("phone_or_email")
        if not value:
            raise ValidationError("This field is required.")
        if "@" not in value and not value.isdigit():
            raise ValidationError("Enter a valid email or phone number.")
        return value

    def clean_otp(self):
        otp = self.cleaned_data.get("otp")
        if not otp or not otp.isdigit() or len(otp) != 6:
            raise ValidationError("Enter a valid 6-digit OTP.")
        # Optional: Add logic to verify OTP from backend/session
        return otp