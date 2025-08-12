# users/utils/messaging.py

import logging
from django.conf import settings
from django.core.mail import send_mail
from twilio.rest import Client

logger = logging.getLogger(__name__)


def send_otp_to_user(destination: str, code: str, via: str = "sms") -> bool:
    """
    Sends a one-time password (OTP) to a user via SMS or email.

    Args:
        destination (str): Recipient contact info — e.g., "+15551234567" or "user@example.com"
        code (str): 6-digit OTP code
        via (str): Delivery method: "sms" or "email"

    Returns:
        bool: True if the OTP was sent successfully, False otherwise.
    """
    try:
        if via == "sms":
            logger.info(f"Sending SMS OTP {code} to {destination}")
            # Twilio integration — ensure these are set in your settings or environment
            account_sid = settings.TWILIO_ACCOUNT_SID
            auth_token = settings.TWILIO_AUTH_TOKEN
            from_number = settings.TWILIO_FROM_NUMBER

            client = Client(account_sid, auth_token)
            message = client.messages.create(
                body=f"Your OTP code is: {code}",
                from_=from_number,
                to=destination
            )
            return bool(message.sid)

        elif via == "email":
            logger.info(f"Sending Email OTP {code} to {destination}")
            subject = "Your OTP Code"
            body = f"Use this code to complete your action: {code}"
            from_email = settings.EMAIL_HOST_USER
            recipient_list = [destination]

            sent_count = send_mail(
                subject=subject,
                message=body,
                from_email=from_email,
                recipient_list=recipient_list,
                fail_silently=False
            )
            return sent_count > 0

        else:
            logger.error(f"Unsupported delivery channel: '{via}'")
            return False

    except Exception as error:
        logger.error(f"Failed to send OTP '{code}' to '{destination}' via '{via}': {error}")
        return False