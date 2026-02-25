# utils/notification_sender.py
import os
from twilio.rest import Client
from flask import current_app

from models import db
from models.notification import Notification

def get_twilio_client():
    """
    Initializes and returns the Twilio client.
    Uses credentials from environment variables.
    """
    # --- CRITICAL FIX: Use os.getenv instead of current_app.config.get for env vars ---
    # BEFORE (Incorrect for env vars):
    # TWILIO_ACCOUNT_SID = current_app.config.get('TWILIO_ACCOUNT_SID')
    # TWILIO_AUTH_TOKEN = current_app.config.get('TWILIO_AUTH_TOKEN')
    # AFTER (Correct for env vars):
    TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
    # --- END CRITICAL FIX ---

    if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
        try:
            client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
            return client
        except Exception as e:
            print(f"Error initializing Twilio client: {e}")
            return None
    else:
        print("Twilio credentials (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN) not found in environment variables (.env).")
        return None


def send_whatsapp_notification(to_phone_number, message_body):
    """
    Sends a WhatsApp message using Twilio.

    Args:
        to_phone_number (str): Recipient's phone number in E.164 format (e.g., '+919876543210').
                               The number must be verified in Twilio Sandbox if using trial.
        message_body (str): The text content of the message.

    Returns:
        bool: True if the message was sent successfully, False otherwise.
    """
    # --- CRITICAL FIX: Use os.getenv instead of current_app.config.get for env vars ---
    # BEFORE (Incorrect for env vars):
    # TWILIO_WHATSAPP_NUMBER = current_app.config.get('TWILIO_WHATSAPP_NUMBER')
    # AFTER (Correct for env vars):
    TWILIO_WHATSAPP_NUMBER = os.getenv('TWILIO_WHATSAPP_NUMBER')
    # --- END CRITICAL FIX ---

    if not TWILIO_WHATSAPP_NUMBER:
        print("Twilio WhatsApp number (TWILIO_WHATSAPP_NUMBER) not found in environment variables.")
        return False

    client = get_twilio_client()
    if not client:
        return False

    try:
        # The 'to' number must also be prefixed with 'whatsapp:'
        message = client.messages.create(
            body=message_body,
            from_=TWILIO_WHATSAPP_NUMBER,  # Twilio's WhatsApp-enabled number
            to=f'whatsapp:{to_phone_number}'  # Recipient's number with 'whatsapp:' prefix
        )
        print(f"WhatsApp message sent successfully. SID: {message.sid}")
        return True
    except Exception as e:
        print(f"Error sending WhatsApp notification: {e}")
        # Log the specific Twilio error for debugging
        if hasattr(e, 'code'):
            print(f"Twilio Error Code: {e.code}")
        if hasattr(e, 'msg'):
            print(f"Twilio Error Message: {e.msg}")
        return False

# Example usage (if run directly, for testing):
# if __name__ == "__main__":
#     # Ensure .env is loaded if running standalone
#     # from dotenv import load_dotenv
#     # load_dotenv()
#     success = send_whatsapp_notification(
#         '+919876543210', # Replace with a verified number in Twilio Sandbox
#         'Hello from ZoomCar Clone! This is a test notification.'
#     )
#     if success:
#         print("Test message sent!")
#     else:
#         print("Failed to send test message.")

def send_notification_to_user(user_id, message):
    """Send a notification to a specific user."""
    try:
        if not isinstance(user_id, int) or user_id <= 0:
            print(f"Invalid user_id provided to send_notification_to_user: {user_id}")
            return False
        if not isinstance(message, str) or not message.strip():
            print(f"Invalid message provided to send_notification_to_user: {message}")
            return False

        notification = Notification(
            user_id=user_id,
            message=message.strip()[:255]
        )
        db.session.add(notification)
        db.session.commit()
        print(f"Notification sent to user {user_id}: {message[:50]}...")
        return True

    except Exception as e:
        db.session.rollback()
        print(f"Error sending notification to user {user_id}: {e}")
        return False

def send_notification_to_host(host_user_id, message):
    """Send a notification to a specific host (via their user account)."""
    try:
        if not isinstance(host_user_id, int) or host_user_id <= 0:
            print(f"Invalid host_user_id provided to send_notification_to_host: {host_user_id}")
            return False
        if not isinstance(message, str) or not message.strip():
            print(f"Invalid message provided to send_notification_to_host: {message}")
            return False

        notification = Notification(
            user_id=host_user_id,
            message=message.strip()[:255]
        )
        db.session.add(notification)
        db.session.commit()
        print(f"Notification sent to host (user_id={host_user_id}): {message[:50]}...")
        return True

    except Exception as e:
        db.session.rollback()
        print(f"Error sending notification to host (user_id={host_user_id}): {e}")
        return False