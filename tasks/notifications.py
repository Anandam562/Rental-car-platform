# tasks/notifications.py
import threading
import time
from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler

from models import db
from models.booking import Booking
from utils.notification_sender import send_notification_to_user
from flask import current_app

def send_pre_trip_reminders():
    """Send pre-trip reminder notifications."""
    with db.app.app_context(): # Ensure app context is available
        try:
            now = datetime.utcnow()
            # Find bookings that are paid/approved/active and within the reminder window
            upcoming_bookings = Booking.query.filter(
                Booking.status.in_(['paid', 'approved', 'active']),
                Booking.start_date >= now,
                Booking.start_date <= (now + timedelta(hours=3)) # Check up to 3 hours ahead
            ).all()

            for booking in upcoming_bookings:
                time_to_start = booking.start_date - now
                hours_diff = time_to_start.total_seconds() / 3600

                if 1.9 <= hours_diff < 2.1: # Approximately 2 hours
                    message = f"Reminder: Your trip for {booking.car.make} {booking.car.model} (Booking #{booking.id}) starts in 2 hours!"
                    send_notification_to_user(user_id=booking.user_id, message=message)
                elif 0.9 <= hours_diff < 1.1: # Approximately 1 hour
                    message = f"Reminder: Your trip for {booking.car.make} {booking.car.model} (Booking #{booking.id}) starts in 1 hour!"
                    send_notification_to_user(user_id=booking.user_id, message=message)
        except Exception as e:
            print(f"Error in send_pre_trip_reminders: {e}")

def send_post_trip_reminder(booking):
    """Send post-trip reminder notifications."""
    try:
        # Use effective end date (original or extended)
        effective_end_date = booking.extension_new_end_date if booking.extension_new_end_date else booking.end_date
        time_to_end = effective_end_date - datetime.utcnow()
        hours_diff = time_to_end.total_seconds() / 3600

        if 1.9 <= hours_diff < 2.1: # Approximately 2 hours before end
            message = f"Reminder: Your trip for {booking.car.make} {booking.car.model} (Booking #{booking.id}) ends in 2 hours!"
            send_notification_to_user(user_id=booking.user_id, message=message)
            current_app.logger.info(f"Sent 2-hour post-trip reminder for booking {booking.id}")
        elif 0.9 <= hours_diff < 1.1: # Approximately 1 hour before end
            message = f"Reminder: Your trip for {booking.car.make} {booking.car.model} (Booking #{booking.id}) ends in 1 hour!"
            send_notification_to_user(user_id=booking.user_id, message=message)
            current_app.logger.info(f"Sent 1-hour post-trip reminder for booking {booking.id}")
    except Exception as e:
        current_app.logger.error(f"Error sending post-trip reminder for booking {booking.id}: {e}")


def send_pre_trip_reminder(booking):
    pass


def check_and_send_timed_notifications():
    """Main function to check for timed events and send notifications."""
    with current_app.app_context(): # Ensure Flask app context is available
        try:
            current_app.logger.info("Checking for timed notifications...")
            now = datetime.utcnow()
            # Find bookings that are paid/approved/active and within the reminder window
            upcoming_bookings = Booking.query.filter(
                Booking.status.in_(['paid', 'approved', 'active']),
                Booking.start_date >= now, # Only future/present start dates
                Booking.start_date <= (now + timedelta(hours=3)) # Check up to 3 hours ahead
            ).all()

            ending_soon_bookings = Booking.query.filter(
                Booking.status.in_(['active']),
                # Use effective end date for reminders
                db.or_(
                    Booking.end_date >= now,
                    Booking.extension_new_end_date >= now
                ),
                # Check up to 3 hours before end (original or extended)
                db.or_(
                    Booking.end_date <= (now + timedelta(hours=3)),
                    Booking.extension_new_end_date <= (now + timedelta(hours=3))
                )
            ).all()

            for booking in upcoming_bookings:
                send_pre_trip_reminder(booking)

            for booking in ending_soon_bookings:
                send_post_trip_reminder(booking)

            current_app.logger.info("Finished checking for timed notifications.")

        except Exception as e:
            current_app.logger.error(f"Error in check_and_send_timed_notifications: {e}")

    # Schedule the next check
    # Run every minute
    timer = threading.Timer(60.0, check_and_send_timed_notifications)
    timer.daemon = True # Dies when main thread dies
    timer.start()

def start_background_scheduler():
    """Start the background notification scheduler."""
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=send_pre_trip_reminders, trigger="interval", minutes=1) # Run every minute
    scheduler.start()
    print("Background notification scheduler started.")

# --- CRITICAL FIX: Status-Based Notifications ---
# These can be triggered directly from model methods or routes when status changes.

# In models/booking.py
# def activate_trip(self):
#     # ... existing logic ...
#     if self.can_be_activated_by_user():
#         # ... update status ...
#         db.session.add(self)
#         db.session.commit() # Commit first
#         # --- Send Trip Started Notification ---
#         send_notification_to_user(
#             user_id=self.user_id,
#             message=f"Your trip for {self.car.make} {self.car.model} (Booking #{self.id}) has started!"
#         )
#         # --- End Send Trip Started Notification ---
#         return True
#     return False

# def complete_trip(self):
#     # ... existing logic ...
#     if self.can_be_completed():
#         # ... update status ...
#         db.session.add(self)
#         db.session.commit() # Commit first
#         # --- Send Trip Completed Notification ---
#         send_notification_to_user(
#             user_id=self.user_id,
#             message=f"Your trip for {self.car.make} {self.car.model} (Booking #{self.id}) has been completed. Thank you!"
#         )
#         # --- Send Trip Completed Notification ---
#         return True
#     return False

# def cancel_by_user(self, reason=""):
#     # ... existing logic ...
#     if self.can_be_cancelled_by_user():
#         # ... update status ...
#         db.session.add(self)
#         db.session.commit() # Commit first
#         # --- Send Trip Cancelled Notification ---
#         send_notification_to_user(
#             user_id=self.user_id,
#             message=f"Your booking #{self.id} for {self.car.make} {self.car.model} has been cancelled. Reason: {reason[:50]}..."
#         )
#         # --- End Send Trip Cancelled Notification ---
#         return True
#     return False
# --- END CRITICAL FIX ---