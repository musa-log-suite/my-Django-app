import pytest
from django.urls import reverse
from users.models import OTP, OTPAttempt

@pytest.mark.django_db
class TestUserViews:

    def test_register_user_triggers_otp(monkeypatch, api_client):
        monkeypatch.setattr(
            "users.services.otp_services.generate_otp_for_user",
            lambda user, purpose: OTP.objects.create(
                user=user,
                code="999999",
                purpose=purpose,
                expires_at=now() + timedelta(minutes=5),
                is_used=False
            )
        )
        payload = {
            "email": "new@example.com",
            "password": "StrongPass123!",
            "phone_number": "+15559876543",
        }
        url = reverse("user-register")
        response = api_client.post(url, payload, format="json")
        assert response.status_code == 201
        assert "OTP sent" in response.json().get("message")

    def test_resend_otp_endpoint(monkeypatch, api_client, user):
        # Stub generate so we don’t actually dispatch
        monkeypatch.setattr(
            "users.services.otp_services.generate_otp_for_user",
            lambda u, purpose: OTP.objects.create(
                user=u,
                code="888888",
                purpose=purpose,
                expires_at=now() + timedelta(minutes=5),
                is_used=False
            )
        )
        url = reverse("resend-otp")
        response = api_client.post(url, {"email": user.email}, format="json")
        assert response.status_code == 200
        assert response.json()["message"] == "OTP resent successfully."

    def test_verify_phone_success(api_client, user):
        # Create matching OTP
        otp = OTP.objects.create(
            user=user,
            code="777777",
            purpose="signup",
            expires_at=now() + timedelta(minutes=5),
            is_used=False
        )
        url = reverse("verify-phone")
        response = api_client.post(url, {"email": user.email, "otp": "777777"}, format="json")
        assert response.status_code == 200
        user.refresh_from_db()
        assert user.is_verified
        assert response.json()["message"] == "Phone number verified successfully."

    def test_password_reset_flow(api_client, monkeypatch, user):
        # 1) Request OTP
        monkeypatch.setattr(
            "users.services.otp_services.generate_otp_for_user",
            lambda u, purpose: OTP.objects.create(
                user=u,
                code="555555",
                purpose=purpose,
                expires_at=now() + timedelta(minutes=5),
                is_used=False
            )
        )
        url_req = reverse("request-password-otp")
        resp_req = api_client.post(url_req, {"email": user.email}, format="json")
        assert resp_req.status_code == 200

        # 2) Reset password
        url_reset = reverse("recover-password")
        payload_reset = {
            "email": user.email,
            "otp": "555555",
            "new_password": "NewStrongPass!23"
        }
        resp_reset = api_client.post(url_reset, payload_reset, format="json")
        assert resp_reset.status_code == 200
        assert resp_reset.json()["message"] == "Password reset successful."
        user.refresh_from_db()
        assert user.check_password("NewStrongPass!23")