import pytest
from django.utils.timezone import now, timedelta

from users.services.otp_services import generate_otp_for_user, verify_otp
from users.models import OTP, OTPAttempt

@pytest.mark.django_db
class TestOTPService:

    def test_generate_otp_creates_record_and_dispatch(monkeypatch, user):
        # Stub out sending so it always succeeds
        monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "config.settings")
        monkeypatch.setattr(
            "users.services.otp_services.send_otp_to_user",
            lambda dest, code, via: True
        )

        otp = generate_otp_for_user(user, purpose="signup", expires_minutes=1)
        assert otp.user == user
        assert otp.purpose == "signup"
        assert otp.expires_at > now()
        assert not otp.is_used
        # One OTPAttempt exists only on dispatch failure, so none now
        assert OTPAttempt.objects.count() == 0

    def test_verify_otp_success(user):
        # Create a valid OTP
        otp = OTP.objects.create(
            user=user,
            code="123456",
            purpose="signup",
            expires_at=now() + timedelta(minutes=5),
            is_used=False
        )
        success, message = verify_otp(user, "123456", purpose="signup")
        assert success is True
        assert message == "OTP verified successfully."
        otp.refresh_from_db()
        assert otp.is_used

    def test_verify_otp_invalid_code_logs_attempt(user):
        OTP.objects.create(
            user=user,
            code="111111",
            purpose="signup",
            expires_at=now() + timedelta(minutes=5),
            is_used=False
        )
        success, _ = verify_otp(user, "000000", purpose="signup")
        assert success is False
        assert OTPAttempt.objects.filter(user=user, success=False).exists()

    def test_verify_otp_expired_logs_attempt(user):
        OTP.objects.create(
            user=user,
            code="222222",
            purpose="signup",
            expires_at=now() - timedelta(minutes=1),
            is_used=False
        )
        success, _ = verify_otp(user, "222222", purpose="signup")
        assert success is False
        assert OTPAttempt.objects.filter(user=user, success=False).exists()