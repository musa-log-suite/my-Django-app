import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from users.models import OTP, OTPAttempt

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def user(db):
    """
    Creates an active, unverified user for tests.
    """
    user = User.objects.create_user(
        email="test@example.com",
        password="old_password123",
        phone_number="+15551234567",
        is_active=True,
        is_verified=False
    )
    return user