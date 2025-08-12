from django.db import transaction
from django.utils.timezone import now
from datetime import timedelta
from django.utils.crypto import get_random_string
from django.conf import settings

from users.models import OTP, OTPAttempt, User
from twilio.rest import Client


# ✅ SMS Sender via Twilio
def send_sms(to, message):
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    client.messages.create(
        body=message,
        from_=settings.TWILIO_PHONE_NUMBER,
        to=to
    )


# ✅ OTP Dispatcher
def send_otp_to_user(destination, code, via='sms'):
    """
    Sends OTP to user via SMS or email.
    Returns True on success, False on failure.
    """
    try:
        if via == 'sms':
            send_sms(destination, f"Your OTP is: {code}")
            return True
        elif via == 'email':
            # You can implement email sending here if needed
            # For now, simulate success
            print(f"📧 Email OTP to {destination}: {code}")
            return True
        else:
            return False
    except Exception as e:
        print(f"❌ Failed to send OTP via {via}: {e}")
        return False


# ✅ OTP Generator
def generate_otp_for_user(user, purpose='signup', expires_minutes=5):
    """
    Creates and dispatches a one-time password (OTP) for a user.
    Returns the OTP instance on success or raises RuntimeError on failure.
    """
    code = get_random_string(length=6, allowed_chars='0123456789')
    expires_at = now() + timedelta(minutes=expires_minutes)

    # Choose channel based on purpose
    if purpose in ('signup', 'login'):
        destination = user.phone_number
        channel = 'sms'
    else:
        destination = user.email
        channel = 'email'

    with transaction.atomic():
        otp_obj = OTP.objects.create(
            user=user,
            code=code,
            purpose=purpose,
            expires_at=expires_at,
            is_used=False
        )

        sent = send_otp_to_user(destination, code, via=channel)
        if not sent:
            OTPAttempt.objects.create(user=user, code_entered='', success=False)
            otp_obj.delete()
            raise RuntimeError(f"Failed to send OTP via {channel}")

    return otp_obj


# ✅ OTP Verifier
def verify_otp(user, code, purpose='signup'):
    """
    Verifies a one-time password (OTP) for a user.
    Logs each attempt with the entered code, marks the OTP as used on success.
    Returns (success: bool, message: str)
    """
    otp_obj = (
        OTP.objects
        .filter(user=user, purpose=purpose, is_used=False)
        .order_by('-created_at')
        .first()
    )

    if not otp_obj:
        OTPAttempt.objects.create(user=user, code_entered=code, success=False)
        return False, 'No valid OTP found.'

    if otp_obj.expires_at < now():
        OTPAttempt.objects.create(user=user, code_entered=code, success=False)
        return False, 'OTP has expired.'

    if otp_obj.code != code:
        OTPAttempt.objects.create(user=user, code_entered=code, success=False)
        return False, 'Invalid OTP.'

    otp_obj.is_used = True
    otp_obj.save(update_fields=['is_used'])
    OTPAttempt.objects.create(user=user, code_entered=code, success=True)

    return True, 'OTP verified successfully.'


# ✅ OTP Dispatcher by Identifier
def send_otp(identifier, purpose='signup'):
    """
    Wrapper to send OTP using either phone number or email.
    Looks up the user and calls generate_otp_for_user().
    """
    user = (
        User.objects.filter(phone_number=identifier).first()
        or User.objects.filter(email=identifier).first()
    )

    if not user:
        raise RuntimeError("User not found for OTP dispatch.")

    return generate_otp_for_user(user, purpose=purpose)