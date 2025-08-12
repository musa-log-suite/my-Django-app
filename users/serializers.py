from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from users.models import User
from users.services.otp_services import send_otp, verify_otp


# ─────────────────────────────────────────────────────────────
# ✅ User Registration Serializer
# ─────────────────────────────────────────────────────────────

class UserRegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for registering a new user with OTP phone verification.
    Validates password confirmation and applies password validators.
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password2 = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    otp = serializers.CharField(
        write_only=True,
        required=True,
        max_length=6,
        help_text="Enter the OTP sent to your phone number"
    )

    class Meta:
        model = User
        fields = [
            'email',
            'phone_number',
            'full_name',
            'is_agent',
            'password',
            'password2',
            'otp',
        ]
        extra_kwargs = {
            'email': {'required': True},
            'phone_number': {'required': True},
            'full_name': {'required': False},
            'is_agent': {'required': False},
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Passwords must match."})

        try:
            validate_password(attrs['password'])
        except DjangoValidationError as e:
            raise serializers.ValidationError({"password": list(e.messages)})

        phone = attrs['phone_number']
        otp_code = attrs['otp']

        success, message = verify_otp(phone, otp_code, purpose="signup")
        if not success:
            raise serializers.ValidationError({"otp": message})

        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        validated_data.pop('otp')

        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            phone_number=validated_data['phone_number'],
            full_name=validated_data.get('full_name', ''),
            is_agent=validated_data.get('is_agent', False)
        )

        return user


# ─────────────────────────────────────────────────────────────
# 🔐 Password Reset Request Serializer
# ─────────────────────────────────────────────────────────────

class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Handles password reset request by sending OTP to user's phone or email.
    """
    identifier = serializers.CharField(required=True)

    def validate_identifier(self, value):
        user = (
            User.objects.filter(phone_number=value).first()
            or User.objects.filter(email=value).first()
        )
        if not user:
            raise serializers.ValidationError("No user found with this phone or email.")
        return value

    def save(self):
        identifier = self.validated_data['identifier']
        send_otp(identifier, purpose="password_reset")


# ─────────────────────────────────────────────────────────────
# 🔑 Password Reset Confirmation Serializer
# ─────────────────────────────────────────────────────────────

class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Verifies OTP and resets user's password using phone or email.
    """
    identifier = serializers.CharField(required=True)
    otp = serializers.CharField(required=True, max_length=6)
    new_password = serializers.CharField(write_only=True)
    new_password2 = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({"new_password": "Passwords must match."})

        try:
            validate_password(attrs['new_password'])
        except DjangoValidationError as e:
            raise serializers.ValidationError({"new_password": list(e.messages)})

        success, message = verify_otp(attrs['identifier'], attrs['otp'], purpose="password_reset")
        if not success:
            raise serializers.ValidationError({"otp": message})

        return attrs

    def save(self):
        user = (
            User.objects.filter(phone_number=self.validated_data['identifier']).first()
            or User.objects.filter(email=self.validated_data['identifier']).first()
        )
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user