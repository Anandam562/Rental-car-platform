# models/booking.py
from sqlalchemy.orm import relationship
import pytz

from utils.notification_sender import send_notification_to_host, send_notification_to_user
from utils.timezone import get_current_ist_time, UTC_TZ, utc_to_ist
from . import db
from datetime import datetime, timedelta

# At the top, add:
from .photo import Photo # Import the Photo model


# --- CRITICAL FIX: Import Feedback Models and Define Availability Flag ---
# Import HostRating and HostFeedback for checking existing feedback
# Make sure the path is correct relative to your project structure.
# If models is a top-level package, this should work:
try:
    from models.host_rating import HostRating
    from models.host_feedback import HostFeedback
    # --- Define the availability flag as True if imports succeed ---
    FEEDBACK_MODELS_AVAILABLE = True
    # --- END Define availability flag ---
except ImportError as e:
    # Handle the case where the feedback models are missing or misconfigured
    print(f"Warning: Could not import feedback models (HostRating, HostFeedback): {e}")
    # --- Define the availability flag as False if imports fail ---
    FEEDBACK_MODELS_AVAILABLE = False
    # --- END Define availability flag ---

    # Fallback definitions to prevent NameError in can_be_activated_by_user
    # These are just placeholders and will raise NotImplementedError if used
    class HostRating:
        pass
    class HostFeedback:
        pass
# --- END CRITICAL FIX ---
# --- CRITICAL FIX: Import timezone utilities ---
# Place these imports near the top of the file, after other imports
# Ensure the path 'utils.timezone' is correct for your project structure.
# This assumes 'utils' is a top-level package/directory in your project.
try:
    from utils.timezone import get_current_ist_time, db_utc_to_ist
    TIMEZONE_UTILS_AVAILABLE = True
    # print("DEBUG: Timezone utilities imported successfully.") # Optional debug print

except ImportError as e:
    # Handle the case where the utils module is missing or misconfigured
    print(f"Warning: Could not import timezone utilities: {e}")
    TIMEZONE_UTILS_AVAILABLE = False

    # --- CRITICAL FIX: Provide fallback implementations or signal error ---
    # Option 1: Define stub functions that raise an error if called
    # This forces the issue to be addressed.
    def get_current_ist_time():
        raise NotImplementedError("Timezone utilities (utils.timezone) are required but not available. Cannot get current IST time.")

    def db_utc_to_ist(dt):
        raise NotImplementedError("Timezone utilities (utils.timezone) are required but not available. Cannot convert DB UTC to IST.")

    # Option 2: Fallback to UTC logic (NOT recommended for consistency, but avoids crash)
    # Uncomment the block below if you prefer this temporary fallback.
    '''
    def get_current_ist_time():
        # Fallback: Just return UTC time (incorrect for IST logic)
        print("Warning: Timezone utilities not available, using UTC for 'current IST time'.")
        utc_now = datetime.utcnow()
        return pytz.utc.localize(utc_now) # Return UTC datetime

    def db_utc_to_ist(db_utc_dt):
        # Fallback: Treat DB time as UTC (incorrect if DB stores UTC, logic expects IST comparison)
        print("Warning: Timezone utilities not available, treating DB UTC time as UTC.")
        if db_utc_dt.tzinfo is None:
            return pytz.utc.localize(db_utc_dt) # Localize as UTC if naive
        return db_utc_dt # Return as-is if already timezone-aware
    '''
    # --- END CRITICAL FIX ---
# --- END CRITICAL FIX: Import timezone utilities ---


class Booking(db.Model):
    __tablename__ = 'bookings'

    id = db.Column(db.Integer, primary_key=True)

    # --- Core Booking Information ---
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    car_id = db.Column(db.Integer, db.ForeignKey('cars.id'), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    total_price = db.Column(db.Float, nullable=False)  # Price for original duration
    # --- End Core Info ---
    # --- CRITICAL FIX: Ensure these fields exist ---
    is_active = db.Column(db.Boolean, default=False)  # Trip is currently active
    is_completed = db.Column(db.Boolean, default=False)  # Trip is completed
    # --- END CRITICAL FIX ---
    # --- Booking Flow Status Fields ---
    # General status of the booking process
    status = db.Column(db.String(20), default='pending') # pending, paid, active, completed, cancelled, extended
    # host_approval = db.Column(db.Boolean, default=False) # REMOVED: Not needed for initial booking
    payment_status = db.Column(db.String(20), default='pending') # pending, completed, failed
    payment_date = db.Column(db.DateTime)
    # --- End Status Fields ---

    # --- Cancellation Details ---
    cancelled_by = db.Column(db.String(10)) # 'user', 'host', 'admin'
    cancellation_reason = db.Column(db.String(255))
    cancellation_fee_deducted = db.Column(db.Float, default=0.0)
    refund_amount = db.Column(db.Float, default=0.0)
    cancelled_at = db.Column(db.DateTime)
    # --- End Cancellation Details ---
    ##trip_photos = relationship('TripPhoto', back_populates='booking', lazy=True)
    # --- Razorpay Integration Fields ---
    # Store Razorpay identifiers for verification and reference
    razorpay_order_id = db.Column(db.String(50)) # Store Razorpay Order ID
    razorpay_payment_id = db.Column(db.String(50)) # Store Razorpay Payment ID (after success)
    # --- End Razorpay Fields ---

    # --- CRITICAL: Trip Extension Fields ---
    # Flag to indicate if an extension request exists
    has_extension_request = db.Column(db.Boolean, default=False)
    # Details of the requested extension
    extension_new_end_date = db.Column(db.DateTime) # Proposed new end date
    extension_additional_days = db.Column(db.Integer) # Calculated additional days
    extension_additional_price = db.Column(db.Float) # Calculated additional price
    # Host approval for extension
    extension_host_approval = db.Column(db.Boolean, default=False)
    extension_host_approval_timestamp = db.Column(db.DateTime)
    # Status for the extension part of the booking
    extension_status = db.Column(db.String(20), default='none') # none, requested, approved, paid, completed, cancelled
    # Razorpay order/payment IDs for extension payment (if separate)
    extension_razorpay_order_id = db.Column(db.String(50))
    extension_razorpay_payment_id = db.Column(db.String(50))
    extension_payment_status = db.Column(db.String(20), default='none') # none, pending, completed, failed
    extension_payment_date = db.Column(db.DateTime)
    # --- END CRITICAL ---

    # --- Timestamps ---
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # --- End Timestamps ---

    # --- REMOVED: Redundant Fields ---
    # is_active = db.Column(db.Boolean, default=False) # Trip is currently active - Use status instead
    # is_completed = db.Column(db.Boolean, default=False) # Trip is completed - Use status instead
    # pickup_photos_json = db.Column(db.Text)  # Store as JSON string - Use Photo model instead
    # dropoff_photos_json = db.Column(db.Text)  # Store as JSON string - Use Photo model instead
    # --- END REMOVED ---

    # --- Relationship Definitions ---
    # DO NOT DEFINE 'user' or 'car' relationships here if Car/Location/User models use backref.
    # The backref on Car.bookings creates a 'car' attribute on Booking instances.
    # The backref on User.bookings creates a 'user' attribute on Booking instances.
    # The relationship to Photo is defined via the Photo model's backref (e.g., booking.photos)
    # --- End Relationships ---

    def __repr__(self):
        return f'<Booking {self.id}>'

    # --- CRITICAL FIX: Define the duration_hours property ---
    @property
    def duration_hours(self):
        """Calculate booking duration in hours."""
        if self.start_date and self.end_date:
            duration = self.end_date - self.start_date
            return duration.total_seconds() / 3600  # Convert seconds to hours
        return 0.0  # Return 0 if dates are not set

    # --- Updated Price Calculation (Alternative: Query Car Directly) ---
    def calculate_total_price(self):
        """Calculate the total price based on duration in hours and car's price per hour."""
        duration_hours = self.duration_hours
        if duration_hours <= 0:
            return 0.0

        # --- CRITICAL FIX 3: Query Car's Price Directly ---
        # This avoids relying on the lazy-loaded relationship potentially being None
        # at the time of the hook execution.
        from .car import Car  # Import Car model inside the method
        car = Car.query.get(self.car_id)  # Fetch the car object using the foreign key
        if not car:
            # Log an error or raise an exception if the car doesn't exist
            print(f"ERROR: Car with ID {self.car_id} not found for booking {self.id}")
            return 0.0  # Or raise an exception

        price_per_hour = car.price_per_hour
        # --- END CRITICAL FIX 3 ---

        return round(duration_hours * price_per_hour, 2)  # Round to 2 decimal places

    def update_price_before_save(self):
        """Call this method before committing the booking to update the total_price."""
        self.total_price = self.calculate_total_price()

    # --- End Updated Price Calculation (Alternative) ---
    # --- End Updated Price Calculation ---
    # --- CRITICAL: Updated Booking State Logic ---
    # --- Initial Booking Logic ---
    def can_be_paid(self):
        """Check if booking can be paid by user (Initial booking payment)."""
        # Payment can be made if booking is pending and payment is also pending
        return self.status == 'pending' and self.payment_status == 'pending'

    def mark_as_paid(self, razorpay_payment_id=None):
        """Mark the booking as paid after successful initial payment."""
        if self.can_be_paid():
            self.payment_status = 'completed'
            self.payment_date = datetime.utcnow()
            self.status = 'paid'  # Status changes to 'paid' after payment
            if razorpay_payment_id:
                self.razorpay_payment_id = razorpay_payment_id
            db.session.add(self)
            return True
        return False

    def mark_payment_failed(self, razorpay_payment_id=None):
        """Mark the booking payment as failed."""
        self.payment_status = 'failed'
        self.status = 'pending'  # Or 'failed'? Depends on policy
        if razorpay_payment_id:
            self.razorpay_payment_id = razorpay_payment_id  # Store failed payment ID for debugging
        db.session.add(self)
        # Don't commit here, let caller handle it

    # --- End Initial Booking Logic ---

    # --- NEW: Trip Activation and Completion Logic (Using Status) ---
    # models/booking.py (Inside the Booking class)

    # --- CRITICAL FIX: Update Booking Activation Logic ---
    # models/booking.py (Inside the Booking class)

    # models/booking.py (Inside the Booking class)
    # Import the utility functions
    # Make sure the path is correct relative to your project structure
    # If utils is a top-level package, this should work:
    from utils.timezone import get_current_ist_time, db_utc_to_ist

    # --- CRITICAL FIX: Update Booking Activation Logic to use IST ---
    # --- CRITICAL FIX: Update Booking Activation Logic to use IST ---
    # --- CRITICAL FIX: Update Booking Activation Logic for DB stored as IST ---
    def can_be_activated_by_user(self):
        """
        Check if user can activate the trip (upload pickup photos and start).
        Assumes start_date and end_date in the database are stored as IST.
        Allows activation if:
        1. The booking status is 'paid'.
        2. The current time in IST is past the booking's start date.
        """
        # --- CRITICAL FIX: Get Current Time in IST ---
        # Use the utility function to get the current IST time
        # Ensure TIMEZONE_UTILS_AVAILABLE is correctly defined/imported as before
        if not TIMEZONE_UTILS_AVAILABLE:
            # Fallback or error handling (adjust as needed)
            print("Warning: Timezone utilities not available, falling back to potentially incorrect UTC comparison.")
            now_utc = datetime.utcnow()
            # INCORRECTLY assume self.start_date is UTC for fallback
            return (
                    self.status == 'paid' and
                    now_utc >= self.start_date
            )
        now_ist = get_current_ist_time()  # Returns timezone-aware IST datetime
        # --- END CRITICAL FIX ---

        # --- CRITICAL FIX: Correctly Interpret DB IST start_date ---
        # The database stores start_date as a naive datetime representing IST.
        # We need to inform Python that this datetime is in IST.
        if not TIMEZONE_UTILS_AVAILABLE:
            # Fallback: Treat DB time as naive IST (still better than UTC if DB is IST)
            # This is a simplification; pytz.localize is preferred for robustness.
            # For a quick fix, we compare naive datetimes.
            # Get current IST time as naive datetime for comparison
            naive_now_ist = datetime.now(pytz.timezone('Asia/Kolkata')).replace(tzinfo=None)
            naive_booking_start_ist = self.start_date  # Already naive, assumed IST
            status_ok = self.status == 'paid'
            time_ok = naive_now_ist >= naive_booking_start_ist
            print(f"DEBUG (Fallback - Naive IST) can_be_activated_by_user - Booking ID: {self.id}")
            print(f"  Status: {self.status}, Required: 'paid', Match: {status_ok}")
            print(
                f"  Now (Naive IST): {naive_now_ist}, Booking Start (Naive IST): {naive_booking_start_ist}, Time OK (Now >= Start): {time_ok}")
            print(f"  Final Result: {status_ok and time_ok}")
            return status_ok and time_ok
        else:
            # Use the robust timezone utility
            try:
                # Import pytz inside the method or at the top of the file
                import pytz
                ist_tz = pytz.timezone('Asia/Kolkata')

                # 1. Localize the naive DB datetime as IST
                # This tells Python that the datetime value represents IST.
                booking_start_ist = ist_tz.localize(self.start_date)
                # --- END CRITICAL FIX ---

                # --- CRITICAL FIX: Perform comparison in IST ---
                # Now compare the timezone-aware IST datetimes
                status_ok = self.status == 'paid'
                time_ok = now_ist >= booking_start_ist  # Compare IST times

                # Debugging output (optional, remove in production)
                print(f"DEBUG can_be_activated_by_user - Booking ID: {self.id}")
                print(f"  Status: {self.status}, Required: 'paid', Match: {status_ok}")
                print(f"  Now (Aware IST): {now_ist}, Booking Start (Localized Aware IST): {booking_start_ist}, Time OK (Now >= Start): {time_ok}")
                print(f"  Final Result: {status_ok and time_ok}")

                return status_ok and time_ok
            except Exception as e:
                # Handle potential errors in localization (e.g., ambiguous/non-existent times)
                print(f"Error in can_be_activated_by_user during localization: {e}")
                return False  # Or handle differently
        # --- END CRITICAL FIX ---

    # --- END CRITICAL FIX ---

    # --- END CRITICAL FIX ---

    # Ensure activate_trip uses the updated check (it should already if it calls can_be_activated_by_user)
    def activate_trip(self):
        """
        Activate the trip after user uploads pickup photos.
        This changes the booking status to 'active'.
        """
        # --- CRITICAL FIX: Use the updated can_be_activated_by_user check ---
        if self.can_be_activated_by_user():  # Use the corrected method that works in IST
            # --- END CRITICAL FIX ---
            self.status = 'active'  # Change status to active
            # is_active and is_completed flags are potentially redundant with status
            # but setting them for completeness based on your model definition
            self.is_active = True
            self.is_completed = False  # Ensure it's not marked completed prematurely
            db.session.add(self)  # Add the modified object to the session

            # --- CRITICAL FIX: Send notification to user ---
            send_notification_to_user(
                user_id=self.user_id,
                message=f"Your trip for {self.car.make} {self.car.model} (Booking #{self.id}) has started!"
            )
            # --- END CRITICAL FIX ---

            # --- CRITICAL FIX: Send notification to host ---
            host_user_id = self.car.host.user_id  # Get the host's user ID
            send_notification_to_host(
                host_user_id=host_user_id,
                message=f"A trip for your {self.car.make} {self.car.model} (Booking #{self.id}) has started!"
            )
            # --- END CRITICAL FIX ---
            # --- END CRITICAL FIX ---

            return True  # Indicate successful activation
        return False  # Indicate activation not allowed

    # --- END activate_trip ---

    # --- END activate_trip ---

    def can_be_completed_by_user(self):
        """Check if user can complete the trip."""
        # Trip can be completed if it's currently active
        return self.status == 'active'

    def complete_trip(self):
        """Complete the trip after user optionally uploads dropoff photos."""
        # This method should only be called from the route after photo upload validation (if any)
        # The route will check can_be_completed_by_user() first.
        if self.status == 'active': # Primary check
            self.status = 'completed' # Change status to completed
            # Transfer earnings to host's wallet (assuming logic exists in Host model)
            host = self.car.host
            if host:
                # Example: Add 90% of total price to host's wallet
                host_earning = self.total_price * 0.9
                # Add extension earnings if applicable
                if self.extension_additional_price:
                    host_earning += self.extension_additional_price * 0.9
                host.add_to_wallet(host_earning)
            db.session.add(self)

            # --- CRITICAL FIX: Send notification to user ---
            # --- CRITICAL FIX: Send notification to user ---
            send_notification_to_user(
                user_id=self.user_id,
                message=f"Your trip for {self.car.make} {self.car.model} (Booking #{self.id}) has been completed. Thank you!"
            )
            # --- END CRITICAL FIX ---

            # --- CRITICAL FIX: Send notification to host ---
            host_user_id = self.car.host.user_id  # Get the host's user ID
            send_notification_to_host(
                host_user_id=host_user_id,
                message=f"The trip for your {self.car.make} {self.car.model} (Booking #{self.id}) has been completed."
            )
            # --- END CRITICAL FIX ---
            # --- END CRITICAL FIX ---
            return True
        return False # Should not happen if route checks properly

    def can_be_completed(self):
        """Check if booking trip can be marked as completed (e.g., drop-off time passed automatically - NOT USED HERE)."""
        # This old method is now redundant with the user-driven completion logic.
        # The trip completion should be driven by the user uploading dropoff photos.
        # The dashboard timer can still show "Until Dropoff" based on status == 'active'.
        # We can keep this for potential future auto-completion logic, but it's not the primary path.
        now = datetime.utcnow()
        # For extensions: Check against the *actual* end date (original or extended)
        effective_end_date = self.extension_new_end_date if self.extension_new_end_date else self.end_date
        return (self.status == 'active' and
                effective_end_date < now)
    # --- End NEW: Trip Activation and Completion Logic ---

    # --- Cancellation Logic ---
    def can_be_cancelled_by_user(self):
        """Check if user can cancel the booking."""
        now = datetime.utcnow()
        time_to_start = self.start_date - now
        # Allow cancellation if payment is pending, or if paid but trip hasn't started, and > 6 hours to start
        return ((self.status == 'pending' and self.payment_status == 'pending') or
                (self.payment_status == 'completed' and self.status in ['paid', 'approved'] and self.status != 'active' and time_to_start > timedelta(hours=6))) # Added check for status != 'active'

    def cancel_by_user(self, reason=""):
        """Cancel the booking by the user."""
        if self.can_be_cancelled_by_user():
            self.status = 'cancelled' # Update status
            self.cancelled_by = 'user'
            self.cancellation_reason = reason[:255]  # Truncate reason
            self.cancelled_at = datetime.utcnow()

            # Deduct cancellation fee if paid
            if self.payment_status == 'completed':
                # Example: 50% cancellation fee
                fee = self.total_price * 0.5
                self.cancellation_fee_deducted = round(fee, 2)
                self.refund_amount = round(self.total_price - fee, 2)

                # Update host wallet (deduct earnings, add back 50%)
                host = self.car.host
                if host:
                    # Deduct full amount first (as it was added on payment)
                    host.deduct_from_wallet(self.total_price)
                    # Add back 50% (host keeps 50% as cancellation fee)
                    host.add_to_wallet(self.total_price * 0.5)
            else:
                # If not paid, no fee/refund
                self.cancellation_fee_deducted = 0.0
                self.refund_amount = 0.0

            db.session.add(self)

            # --- CRITICAL FIX: Send notification to user ---
            # --- CRITICAL FIX: Send notification to user ---
            send_notification_to_user(
                user_id=self.user_id,
                message=f"Your booking #{self.id} for {self.car.make} {self.car.model} has been cancelled. Reason: {reason[:50]}..."
            )
            # --- END CRITICAL FIX ---

            # --- CRITICAL FIX: Send notification to host ---
            host_user_id = self.car.host.user_id  # Get the host's user ID
            send_notification_to_host(
                host_user_id=host_user_id,
                message=f"A booking #{self.id} for your {self.car.make} {self.car.model} has been cancelled by the user. Reason: {reason[:50]}..."
            )
            # --- END CRITICAL FIX ---
            # --- END CRITICAL FIX ---

            return True
        return False

    def can_be_cancelled_by_host(self):
        """Check if host can cancel the booking (before pickup)."""
        # Host can cancel before payment or within a window before trip start
        now = datetime.utcnow()
        time_to_start = self.start_date - now
        return ((self.status in ['pending'] and self.payment_status == 'pending') or
                (self.payment_status == 'completed' and self.status in ['paid', 'approved'] and self.status != 'active' and time_to_start > timedelta(hours=1))) # Added check for status != 'active'

    def cancel_by_host(self, reason=""):
        """Cancel the booking by the host."""
        if self.can_be_cancelled_by_host():
            self.status = 'cancelled' # Update status
            self.cancelled_by = 'host'
            self.cancellation_reason = reason[:255]  # Truncate reason
            self.cancelled_at = datetime.utcnow()

            # No cancellation fee for host
            self.cancellation_fee_deducted = 0.0
            self.refund_amount = self.total_price  # Full refund

            # Update host wallet (remove earnings if paid)
            host = self.car.host
            if host and self.payment_status == 'completed':
                host.deduct_from_wallet(self.total_price)

            # Notify Admin (placeholder - implement notification logic)
            self._notify_admin_of_host_cancellation(reason)

            db.session.add(self)
            return True
        return False

    def _notify_admin_of_host_cancellation(self, reason):
        """Placeholder for notifying admin of host cancellation."""
        print(f"[ADMIN NOTIFICATION] Host {self.car.host.user.username} cancelled booking {self.id} for {self.car.make} {self.car.model}. Reason: {reason}")

    # --- End Cancellation Logic ---

    # --- CRITICAL: Trip Extension Logic ---
    def can_request_extension(self):
        """Check if user can request an extension for this booking."""
        # Must be paid/active, not completed, not already have a request, and extension not paid/completed
        return (self.payment_status == 'completed' and
                self.status in ['paid', 'active', 'extended'] and
                self.status != 'completed' and # Explicitly check status
                not self.has_extension_request and
                self.extension_status in ['none', 'cancelled'] and
                self.extension_payment_status in ['none', 'cancelled'])

    def request_extension(self, new_end_date_str):
        """User requests to extend the booking."""
        if not self.can_request_extension():
            return False, "Extension cannot be requested at this time."

        try:
            new_end_date = datetime.strptime(new_end_date_str, '%Y-%m-%d')
        except ValueError:
            return False, "Invalid date format for extension."

        original_end_date = self.extension_new_end_date if self.extension_new_end_date else self.end_date

        # Check if new end date is after original end date
        if new_end_date <= original_end_date:
            return False, "Extension end date must be after the current trip end date."

        # Check if request is made at least 6 hours before original end
        now = datetime.utcnow()
        time_until_original_end = original_end_date - now
        if time_until_original_end < timedelta(hours=6):
            return False, "Extension request must be made at least 6 hours before the original trip end time."

        # Calculate additional days and price
        additional_days = (new_end_date - original_end_date).days
        if additional_days <= 0:
            return False, "Invalid extension duration."

        # Use price_per_hour for extension calculation
        additional_hours = additional_days * 24 # Approximate hours
        additional_price = additional_hours * self.car.price_per_hour # Use price_per_hour

        # Update booking fields for extension request
        self.has_extension_request = True
        self.extension_new_end_date = new_end_date
        self.extension_additional_days = additional_days
        self.extension_additional_price = round(additional_price, 2)
        self.extension_status = 'requested'
        self.extension_payment_status = 'pending'  # Reset payment status for extension
        self.extension_razorpay_order_id = None  # Clear previous order ID
        self.extension_razorpay_payment_id = None  # Clear previous payment ID

        db.session.add(self)
        # Don't commit here, let caller handle it
        return True, "Extension request submitted successfully. Waiting for host approval."

    def can_approve_extension(self, host):
        """Check if host can approve this extension request."""
        # Must be the owner, have a request, and request is in 'requested' status
        return (host.id == self.car.host_id and
                self.has_extension_request and
                self.extension_status == 'requested')

    def approve_extension(self, host):
        """Host approves the extension request."""
        if not self.can_approve_extension(host):
            return False, "Extension approval not allowed."

        # Update extension status
        self.extension_status = 'approved'
        self.extension_host_approval = True
        self.extension_host_approval_timestamp = datetime.utcnow()

        db.session.add(self)
        # Don't commit here, let caller handle it
        return True, "Extension approved. User can now proceed with payment."

    def can_reject_extension(self, host):
        """Check if host can reject this extension request."""
        return self.can_approve_extension(host)  # Same conditions as approval


    def reject_extension(self, host):
        """Host rejects the extension request."""
        if not self.can_reject_extension(host):
            return False, "Extension rejection not allowed."

        # Reset extension fields
        self.has_extension_request = False
        self.extension_new_end_date = None
        self.extension_additional_days = None
        self.extension_additional_price = None
        self.extension_status = 'cancelled'
        self.extension_payment_status = 'none'
        self.extension_razorpay_order_id = None
        self.extension_razorpay_payment_id = None

        db.session.add(self)
        # Don't commit here, let caller handle it
        return True, "Extension request rejected."


    def can_pay_for_extension(self):
        """Check if user can pay for the approved extension."""
        return (self.has_extension_request and
                self.extension_status == 'approved' and
                self.extension_payment_status == 'pending')

    def can_give_feedback(self):
        """
        Check if user can give feedback for this booking.
        Feedback can be given if:
        1. The booking status is 'completed'.
        2. The booking is marked as completed (is_completed is True).
        3. No feedback/rating has been given for this specific booking yet.
        """
        # --- CRITICAL FIX: Check if feedback models are available ---
        if not FEEDBACK_MODELS_AVAILABLE:
            # Fallback or error handling if imports failed
            # For now, fall back to a simple check (might be less accurate)
            # Raising NotImplementedError might be better to force fixing the import
            # raise NotImplementedError("Feedback models are required but not available.")
            # FALLBACK TO SIMPLE CHECK (NOT RECOMMENDED LONG TERM):
            print("Warning: Feedback models not available, falling back to simple status check for feedback eligibility.")
            return (
                self.status == 'completed'
                # self.is_completed == True # Explicitly check is_completed flag
                # Cannot check for existing feedback/rating without models
            )
        # --- END CRITICAL FIX ---

        # --- CRITICAL FIX: Check if booking is completed ---
        # Feedback can only be given for completed bookings
        is_booking_completed = self.status == 'completed' #and self.is_completed == True
        # --- END CRITICAL FIX ---

        # --- CRITICAL FIX: Enhanced Debugging for Feedback Check ---
        # Add detailed debugging information BEFORE the query
        print(f"DEBUG can_give_feedback - Booking ID: {self.id}")
        print(f"  Status: {self.status}, Required: 'completed', Match: {self.status == 'completed'}")
        print(f"  Is Completed Flag: {self.is_completed}, Required: True, Match: {self.is_completed == True}")
        print(f"  Booking Completed Overall: {is_booking_completed}")
        # --- END CRITICAL FIX ---

        # --- CRITICAL FIX: Check if feedback/rating already exists ---
        # Query the database to see if a HostRating or HostFeedback record already exists for this specific booking
        # Use filter_by with booking_id=self.id to ensure specificity
        existing_rating = HostRating.query.filter_by(booking_id=self.id).first()
        existing_feedback = HostFeedback.query.filter_by(booking_id=self.id).first()

        # --- CRITICAL FIX: Enhanced Debugging for Existing Feedback ---
        # Add detailed debugging information AFTER the query
        print(f"  Existing Rating Query Result: {existing_rating}")
        print(f"  Existing Feedback Query Result: {existing_feedback}")
        print(f"  Existing Rating Found: {bool(existing_rating)}")
        print(f"  Existing Feedback Found: {bool(existing_feedback)}")
        # --- END CRITICAL FIX ---

        # Feedback can be given if neither rating nor feedback exists for this specific booking
        no_existing_feedback = not existing_rating and not existing_feedback

        # --- CRITICAL FIX: Enhanced Debugging for Final Result ---
        # Add detailed debugging information for the final result
        print(f"  No Existing Feedback: {no_existing_feedback}")
        print(f"  Final Result (Booking Completed AND No Feedback): {is_booking_completed and no_existing_feedback}")
        # --- END CRITICAL FIX ---

        # --- CRITICAL FIX: Combine conditions ---
        # Return True only if booking is completed and no feedback/rating exists
        return is_booking_completed and no_existing_feedback

    # --- END NEW: Check if Feedback Can Be Given ---

    def mark_extension_paid(self, razorpay_payment_id=None):
        """Mark the extension payment as completed."""
        if self.can_pay_for_extension():
            self.extension_payment_status = 'completed'
            self.extension_payment_date = datetime.utcnow()
            self.extension_razorpay_payment_id = razorpay_payment_id

            # Update main booking end date and total price
            if self.extension_new_end_date:
                self.end_date = self.extension_new_end_date
                self.total_price += self.extension_additional_price
                self.status = 'extended'  # Indicate it's been extended

            db.session.add(self)
            return True
        return False


    def can_complete_extension(self):
        """Check if the extended trip can be marked as completed."""
        # This is handled by the main complete_trip logic now
        # which checks the effective_end_date (could be extended)
        return self.extension_payment_status == 'completed' and self.status == 'active' and not self.status == 'completed' # Redundant check, kept for clarity


    # --- END CRITICAL: Trip Extension Logic ---

    def get_transaction_details(self):
        """Get formatted transaction details for display."""
        details = {
            'booking_id': self.id,
            'total_amount': self.total_price,
            'payment_status': self.payment_status,
            'payment_date': self.payment_date.strftime('%Y-%m-%d %H:%M') if self.payment_date else None,
            'razorpay_payment_id': self.razorpay_payment_id,
            'cancellation_fee': self.cancellation_fee_deducted,
            'refund_amount': self.refund_amount,
            'cancelled_by': self.cancelled_by,
            'cancellation_reason': self.cancellation_reason,
            'cancelled_at': self.cancelled_at.strftime('%Y-%m-%d %H:%M') if self.cancelled_at else None,
            'status': self.status,
            # Add extension details
            'has_extension': self.has_extension_request,
            'extension_status': self.extension_status,
            'extension_new_end_date': self.extension_new_end_date.strftime('%Y-%m-%d') if self.extension_new_end_date else None,
            'extension_additional_days': self.extension_additional_days,
            'extension_additional_price': self.extension_additional_price,
            'extension_payment_status': self.extension_payment_status,
            'extension_razorpay_payment_id': self.extension_razorpay_payment_id,
        }
        return details

    # Inside the Booking class, add these methods (e.g., before or after get_transaction_details):
    def get_pickup_photos(self):
        """Get all pickup photos associated with this booking."""
        # Use the relationship defined in the Photo model (backref='booking')
        return [photo for photo in self.photos if photo.photo_type == 'pickup'] # Assuming 'photos' is the backref name

    def get_dropoff_photos(self):
        """Get all dropoff photos associated with this booking."""
        # Use the relationship defined in the Photo model (backref='booking')
        return [photo for photo in self.photos if photo.photo_type == 'dropoff'] # Assuming 'photos' is the backref name

    def get_min_extension_date(self):
        """Returns the earliest possible date for an extension (1 day after current end date)."""
        return self.end_date + timedelta(days=1)

    # Optional: Also add helper to check if extension is allowed
    def can_be_extended(self):
        """Check if booking is eligible for extension."""
        return self.status in ['active', 'approved'] and self.payment_status == 'completed'

# --- Hook for SQLAlchemy to update price before insert/update ---
# This ensures total_price is always calculated based on current start/end dates and car price
@db.event.listens_for(Booking, 'before_insert')
@db.event.listens_for(Booking, 'before_update')
def update_booking_price(mapper, connection, target):
    target.update_price_before_save()
# --- End Hook ---