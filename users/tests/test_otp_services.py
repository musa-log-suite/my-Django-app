import pytest
from django.utils import timezone
from users.services.otp import verify_otp
from users.models import OneTimePassword

@pytest.mark.django_db
def test_verify_otp_success(user_factory, otp_factory):
    otp = otp_factory(user=user_factory(), code="123456")
    result = verify_otp(phone=otp.phone, code="123456")
    assert result is True

@pytest.mark.django_db
def test_verify_otp_expired(user_factory, otp_factory):
    otp = otp_factory(user=user_factory(), code="654321", expires_at=timezone.now() - timezone.timedelta(minutes=1))
    result = verify_otp(phone=otp.phone, code="654321")
    assert result is False

@pytest.mark.django_db
def test_verify_otp_wrong_code(user_factory, otp_factory):
    otp = otp_factory(user=user_factory(), code="999999")
    result = verify_otp(phone=otp.phone, code="000000")
    assert result is False

@pytest.mark.django_db
def test_verify_otp_after_failed_attempts(user_factory, otp_factory):
    otp = otp_factory(user=user_factory(), code="456789")
    verify_otp(phone=otp.phone, code="111111")
    verify_otp(phone=otp.phone, code="222222")
    result = verify_otp(phone=otp.phone, code="456789")
    assert result is True

@pytest.mark.django_db
def test_verify_otp_invalid_phone(user_factory):
    result = verify_otp(phone="+2340000000000", code="123456")
    assert result is False