# routes/booking.py
import hashlib
import hmac
from datetime import datetime, timedelta
from flask_wtf.csrf import CSRFProtect  # ✅ Keep this if you need CSRF globally
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, current_app
from flask_login import login_required, current_user
from razorpay.errors import SignatureVerificationError

# Import the Booking model correctly from models
from models.booking import Booking # <-- Import from models, not defined here
from models.car import Car
from models import db # Import db for session operations
# Import Razorpay
import razorpay
import os
from models.notification import Notification
from utils.notification_sender import send_notification_to_user

# AFTER (Correct - Import the csrf instance)
# --- END CRITICAL FIX 1 ---
# csrf = CSRFProtect()
booking_bp = Blueprint('booking', __name__, url_prefix='/booking')

# --- Razorpay Client Initialization ---
RAZORPAY_KEY_ID = os.getenv('RAZORPAY_KEY_ID')
RAZORPAY_KEY_SECRET = os.getenv('RAZORPAY_KEY_SECRET')

# Initialize Razorpay client
if RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET:
    try:
        razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
        razorpay_client.set_app_details({"title": "ZoomCarClone", "version": "1.0"})
    except Exception as e:
        current_app.logger.error(f"Error initializing Razorpay client: {e}")
        razorpay_client = None
else:
    current_app.logger.warning("Razorpay keys not found in environment variables.")
    razorpay_client = None
# --- End Razorpay Client ---

# --- Route Definitions ---
# ... (Keep your existing route functions like list_bookings, booking_detail, initiate_booking, process_payment, handle_payment) ...
# Make sure they import Booking from models.booking, not define it.

@booking_bp.route('/')
@login_required
def list_bookings():
    """List user's bookings"""
    bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.created_at.desc()).all()
    return render_template('user/bookings/list.html', bookings=bookings)

from datetime import timedelta

@booking_bp.route('/<int:booking_id>')
@login_required
def booking_detail(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.user_id != current_user.id:
        flash('Access denied')
        return redirect(url_for('car.home'))

    # ✅ CALCULATE min_extension_date HERE — in Python, not template
    min_extension_date = booking.end_date + timedelta(days=1)

    return render_template(
        'user/bookings/detail.html',
        booking=booking,
        min_extension_date=min_extension_date  # ✅ Pass it to template
    )


@booking_bp.route('/initiate/<int:car_id>', methods=['GET']) # <-- ADD GET method
@login_required
def show_booking_initiation(car_id):
    """Display the booking initiation page for a specific car.
    This handles GET requests to '/booking/initiate/<car_id>'.
    """
    car = Car.query.get_or_404(car_id)
    # Calculate default dates (e.g., tomorrow for 2 hours)
    default_start_datetime = datetime.now() + timedelta(hours=1)
    default_end_datetime = default_start_datetime + timedelta(hours=2)

    # Pass car details and default dates to template
    return render_template(
        'booking/initiate.html', # Ensure this template exists
        car=car,
        default_start_datetime=default_start_datetime,
        default_end_datetime=default_end_datetime
    )


# --- END NEW GET ROUTE ---

# --- EXISTING POST ROUTE: Process Booking Initiation ---
@booking_bp.route('/initiate/<int:car_id>', methods=['POST'])
@login_required
def initiate_booking(car_id):
    """Initiate a booking for a specific car."""
    car = Car.query.get_or_404(car_id)

    start_datetime_str = request.form.get('start_datetime')
    end_datetime_str = request.form.get('end_datetime')

    try:
        start_datetime = datetime.strptime(start_datetime_str, '%Y-%m-%dT%H:%M') # Format for datetime-local input
        end_datetime = datetime.strptime(end_datetime_str, '%Y-%m-%dT%H:%M')
    except ValueError:
        flash('Invalid date/time format.')
        return redirect(url_for('booking.show_booking_initiation', car_id=car_id))

    if end_datetime <= start_datetime:
        flash('End date/time must be after start date/time.')
        return redirect(url_for('booking.show_booking_initiation', car_id=car_id))

    # Calculate duration and price (simplified) - Now uses hours
    duration_hours = (end_datetime - start_datetime).total_seconds() / 3600
    if duration_hours <= 0:
        duration_hours = 1
    total_price = round(duration_hours * car.price_per_hour, 2) # Round to 2 decimal places

    # - Core Booking Creation Logic -
    # Check for existing conflicting bookings (simplified)
    existing_booking = Booking.query.filter(
        Booking.car_id == car_id,
        Booking.status.in_(['pending', 'approved', 'paid', 'active']), # Consider different statuses
        Booking.start_date < end_datetime,
        Booking.end_date > start_datetime
    ).first()

    if existing_booking:
        flash('Car is not available for the selected date/time range.')
        # --- Send Booking Failed Notification ---
        send_notification_to_user(
            user_id=current_user.id,
            message=f"Booking failed for {car.make} {car.model}. Car is not available for the selected dates/times."
        )
        # --- End Send Booking Failed Notification ---
        return redirect(url_for('booking.show_booking_initiation', car_id=car_id))

    # Create new booking record
    booking = Booking(
        user_id=current_user.id,
        car_id=car_id,
        start_date=start_datetime, # Store as datetime
        end_date=end_datetime,     # Store as datetime
        # total_price will be set by the SQLAlchemy hook before_insert/before_update
        # total_price=total_price, # Commented out, hook will set it
        status='pending', # Initial status might be pending host approval
        payment_status='pending' # Payment status before payment
        # Add other fields as needed
    )
    # Explicitly call the update method just before adding to session
    # This ensures the price is calculated based on the current values before the hook runs
    booking.update_price_before_save()
    db.session.add(booking)
    db.session.commit()

    flash('Booking initiated! Please complete the payment.')
    # Redirect to payment processing route
    return redirect(url_for('booking.process_payment', booking_id=booking.id))


# --- END EXISTING POST ROUTE ---

@booking_bp.route('/bookings/<int:booking_id>/complete-payment', methods=['POST']) # <-- New Route
@login_required
def complete_payment(booking_id):
    """
    Initiate Razorpay payment for a booking directly.
    This is the 'booking.complete_payment' endpoint.
    """
    booking = Booking.query.get_or_404(booking_id)

    # --- Authorization Check ---
    if booking.user_id != current_user.id:
        flash('Access denied.')
        return redirect(url_for('car.home'))
    # --- End Authorization ---

    # --- Check if Booking can be Paid ---
    if not booking.can_be_paid(): # Assuming you have this method in Booking model
        flash('This booking cannot be paid at this time.')
        return redirect(url_for('booking.booking_detail', booking_id=booking_id))
    # --- End Check ---

    # --- Razorpay Integration ---
    if not razorpay_client:
        flash('Payment gateway is currently unavailable. Please try again later.', 'danger')
        return redirect(url_for('booking.booking_detail', booking_id=booking_id))

    try:
        # Create a Razorpay Order
        order_data = {
            'amount': int(booking.total_price * 100), # Razorpay expects amount in paise
            'currency': 'INR',
            'receipt': f"booking_receipt_{booking.id}",
            'payment_capture': 1 # Auto-capture payment
        }
        razorpay_order = razorpay_client.order.create(order_data)
        razorpay_order_id = razorpay_order['id']

        # Store order ID in booking
        booking.razorpay_order_id = razorpay_order_id
        db.session.commit()

        # --- Prepare Context for Razorpay Checkout Template ---
        context = {
            'booking': booking,
            'razorpay_key_id': RAZORPAY_KEY_ID,
            'razorpay_order_id': razorpay_order_id,
            'total_amount_paise': int(booking.total_price * 100),
            'total_amount_rupees': booking.total_price
        }

        # --- Render Razorpay Checkout Template Directly ---
        # This template will contain the Razorpay Checkout.js script
        return render_template('booking/razorpay_checkout.html', **context)

    except razorpay.errors.RazorpayError as e:
        print(f"Razorpay API error: {e}")
        flash('Failed to initiate payment. Please try again.', 'danger')
        return redirect(url_for('booking.booking_detail', booking_id=booking_id))
    except Exception as e:
        db.session.rollback()
        print(f"Unexpected error in complete_payment: {e}")
        flash('An unexpected error occurred. Please try again.', 'danger')
        return redirect(url_for('booking.booking_detail', booking_id=booking_id))
    # --- End Razorpay Integration ---

# ... (rest of routes/booking.py - handle_payment, etc.) ...


# --- EXISTING PAYMENT ROUTES ---
# routes/booking.py (Relevant part - process_payment function)
# ... (imports and razorpay_client initialization remain the same) ...

@booking_bp.route('/<int:booking_id>/process_payment', methods=['GET'])
@login_required
def process_payment(booking_id):
    """Initiate Razorpay payment for a specific booking.
    This is the 'booking.process_payment' endpoint."""
    booking = Booking.query.get_or_404(booking_id)

    # - Authorization Check -
    if booking.user_id != current_user.id:
        flash('Access denied.')
        return redirect(url_for('car.home'))
    # - End Authorization -

    # - Check if Booking can be Paid -
    if not booking.can_be_paid(): # Assuming you have this method in Booking model
        flash('This booking cannot be paid at this time.')
        return redirect(url_for('booking.booking_detail', booking_id=booking_id))
    # - End Check -

    # - Razorpay Integration -
    if not razorpay_client:
        flash('Payment gateway is currently unavailable. Please try again later.', 'danger')
        return redirect(url_for('booking.booking_detail', booking_id=booking_id))

    try:
        # Create a Razorpay Order
        order_data = {
            "amount": int(booking.total_price * 100),  # Razorpay expects amount in paise
            "currency": "INR",
            "receipt": f"booking_receipt_{booking.id}",
            "payment_capture": 1 # Auto-capture payment
        }
        razorpay_order = razorpay_client.order.create(order_data)
        razorpay_order_id = razorpay_order['id']

        # --- CRITICAL FIX: Store order ID in booking and commit ---
        # This ensures the order ID is saved to the database before the payment popup opens
        booking.razorpay_order_id = razorpay_order_id
        db.session.commit() # This is crucial!
        # --- END CRITICAL FIX ---

        # Prepare context for Razorpay Checkout Template
        context = {
            'booking': booking,
            'razorpay_key_id': RAZORPAY_KEY_ID,
            'razorpay_order_id': razorpay_order_id,
            'total_amount_paise': int(booking.total_price * 100),
            'total_amount_rupees': booking.total_price
        }

        # Render Razorpay Checkout Template Directly
        # This template will contain the Razorpay Checkout.js script
        return render_template('booking/razorpay_checkout.html', **context)

    # - CRITICAL FIX: Catch the correct Razorpay exception -
    # AFTER (Correct - Catch specific known errors or general Exception)
    except razorpay.errors.BadRequestError as e: # Catch specific known Razorpay API errors
        print(f"Razorpay API error (BadRequest): {e}")
        flash(f'Failed to initiate payment: {str(e)}', 'danger')
        return redirect(url_for('booking.booking_detail', booking_id=booking_id))
    except Exception as e: # Catch any other unexpected errors from Razorpay SDK
        db.session.rollback()
        print(f"Unexpected error in process_payment: {e}")
        flash('An unexpected error occurred during payment processing. Please try again.', 'danger')
        return redirect(url_for('booking.booking_detail', booking_id=booking_id))
    # - END CRITICAL FIX -
    # - End Razorpay Integration -


# routes/booking.py (Updated handle_payment route)
# ... (imports and razorpay_client initialization remain the same) ...

# --- EXISTING PAYMENT ROUTES ---
# routes/booking.py (Updated handle_payment route)

@booking_bp.route('/payment-handler', methods=['POST'])
def handle_payment():
    """
    Handle Razorpay payment callback/verification via AJAX from frontend.
    This endpoint receives the payment details from the frontend JS after
    the Razorpay popup closes and verifies the signature before updating the booking.
    """
    current_app.logger.info("handle_payment route called.")

    # --- CRITICAL FIX 1: Ensure CSRF token is present (from frontend AJAX call) ---
    # The frontend JS (razorpaycheckout.html) sends the CSRF token in the headers.
    csrf_token = request.headers.get('X-CSRFToken')
    if not csrf_token:
        current_app.logger.warning("CSRF token missing from payment handler request (X-CSRFToken header).")
        return jsonify({'success': False, 'message': 'CSRF token is missing.'}), 400
    # --- END CRITICAL FIX 1 ---

    # --- CRITICAL FIX 1: Robust Razorpay Client Check ---
    if not razorpay_client:
        current_app.logger.error("Razorpay client is not initialized.")
        # Return JSON error for AJAX handler
        return jsonify(
            {'success': False, 'message': 'Payment gateway is currently unavailable. Please try again later.'}), 500
    # --- END CRITICAL FIX 1 ---

    try:
        # --- CRITICAL FIX 2: Get payment details from JSON request body ---
        data = request.get_json()  # <-- Use get_json() for application/json content-type
        current_app.logger.info(f"Received JSON data: {data}")
        # --- END CRITICAL FIX 2 ---

        # --- CRITICAL FIX 3: Validate required payment data from JSON ---
        if not data:
            current_app.logger.warning("handle_payment received no JSON data.")
            return jsonify({'success': False, 'message': 'Invalid payment data received (No JSON payload).'}), 400

        payment_id = data.get('razorpay_payment_id')
        order_id = data.get('razorpay_order_id')
        signature = data.get('razorpay_signature')

        if not all([payment_id, order_id, signature]):
            current_app.logger.warning(
                f"handle_payment received incomplete JSON data: payment_id={payment_id}, order_id={order_id}, signature={signature}")
            return jsonify(
                {'success': False, 'message': 'Invalid payment data received. Missing required fields.'}), 400
        # --- END CRITICAL FIX 3 ---

        # --- CRITICAL FIX 4: Verify the payment signature using HMAC SHA256 ---
        try:
            # Create the expected signature string
            signature_data = f"{order_id}|{payment_id}"
            # Generate the expected signature using HMAC-SHA256
            expected_signature = hmac.new(
                key=RAZORPAY_KEY_SECRET.encode(),
                msg=signature_data.encode(),
                digestmod=hashlib.sha256
            ).hexdigest()

            # Securely compare the signatures
            if not hmac.compare_digest(expected_signature, signature):
                current_app.logger.warning(f"Payment verification failed: Signature mismatch for order {order_id}.")
                return jsonify({'success': False, 'message': 'Payment verification failed. Signature mismatch.'}), 400

            result = True  # If no exception and signatures match
            current_app.logger.info(f"Payment signature verified successfully for order {order_id}.")
        except Exception as e:
            current_app.logger.error(f"Error during signature verification: {e}")
            return jsonify({'success': False, 'message': f'Payment verification error: {str(e)}'}), 400
        # --- END CRITICAL FIX 4 ---

        if result:
            # Payment signature verified successfully
            # --- CRITICAL FIX 5: Fetch booking by razorpay_order_id ---
            # Find the booking associated with this Razorpay order ID
            booking = Booking.query.filter_by(razorpay_order_id=order_id).first()
            if not booking:
                current_app.logger.warning(f"handle_payment: Booking not found for Razorpay order ID {order_id}")
                # Return 404 JSON for AJAX handler
                return jsonify({'success': False, 'message': 'Booking record not found for this payment.'}), 404
            # --- END CRITICAL FIX 5 ---

            # --- CRITICAL FIX 6: Authorization Check (Frontend JS Call) ---
            # This endpoint is called by the frontend JS *after* payment.
            # The frontend JS runs in the context of the logged-in user.
            # Therefore, `current_user` should be available here.
            # Verify that the booking belongs to the current user.
            if booking.user_id != current_user.id:
                 current_app.logger.warning(f"handle_payment: Access denied for user {current_user.id} on booking {booking.id}")
                 return jsonify({'success': False, 'message': 'Booking not found or access denied.'}), 403 # Use 403 Forbidden
            # --- END CRITICAL FIX 6 ---

            # --- CRITICAL FIX 7: Prevent Double Payment ---
            # Check if booking payment is already completed
            if booking.payment_status == 'completed':
                current_app.logger.info(f"handle_payment: Payment already processed for booking {booking.id}")
                # Already processed - Return success JSON for AJAX handler
                return jsonify({
                    'success': True,
                    'message': 'Payment already processed for this booking.',
                    'redirect_url': url_for('booking.booking_detail', booking_id=booking.id)
                })
            # --- END CRITICAL FIX 7 ---

                # --- CRITICAL FIX 8: Update booking status and host wallet ---
                # BEFORE (Incorrect - Simple status updates)
                # booking.payment_status = 'completed'
                # booking.payment_date = datetime.utcnow()
                # booking.razorpay_payment_id = payment_id # Store payment ID
                # booking.status = 'paid' # Or 'active' if trip starts immediately after payment
                #
                # # - Update Host Wallet -
                # host = booking.car.host
                # if host:
                #     # Example: Add 90% of total price to host's wallet
                #     host_earning = booking.total_price * 0.9
                #     host.add_to_wallet(host_earning)
                #     # You might want to record this in a WalletTransaction model
                # # - End Update Host Wallet -
                # db.session.commit() # Commit changes
                # AFTER (Corrected - Use model methods and record transaction)
                # --- Update Booking ---
                booking.payment_status = 'completed'
                booking.payment_date = datetime.utcnow()
                booking.razorpay_payment_id = payment_id  # Store payment ID
                # Status stays 'paid' until user activates trip
                booking.status = 'paid'
                db.session.add(booking)  # Add booking to session

                # --- Update Host Wallet & Record Transaction ---
                host = booking.car.host
                host_earning = 0.0
                if host:
                    # Calculate host's earning (e.g., 90% of total price)
                    host_earning = round(booking.total_price * 0.9, 2)  # Example: 90%, rounded

                    # Add earning to host's wallet balance (Model method)
                    host.add_to_wallet(host_earning)  # This updates host.wallet_balance

                    # --- CRITICAL FIX: Record Host Earning Transaction ---
                    # Record the earning in the wallet_transactions table
                    WalletTransaction.record_host_earning(
                        host_user=host.user,  # Pass the User object associated with the host
                        booking=booking,
                        earning_amount=host_earning
                    )
                    # --- END CRITICAL FIX ---
                # --- END Update Host Wallet & Record Transaction ---

                # --- CRITICAL FIX: Record User Payment Transaction ---
                # Record the user's payment deduction in the wallet_transactions table
                WalletTransaction.record_booking_payment(
                    user=booking.user,  # Pass the User object who made the booking
                    booking=booking,
                    amount_paid=booking.total_price  # The amount deducted from user's perspective
                )
                # --- END CRITICAL FIX ---

                # --- CRITICAL FIX: Commit Changes ---
                db.session.commit()  # Commit booking update, host wallet update, and transaction records
                # --- END CRITICAL FIX ---
            # --- CRITICAL FIX 8: Update booking status and host wallet ---
            # Use the model's method to mark payment as completed
            # This ensures consistency with the logic defined in the Booking model
            # The total_price used here is already calculated based on hours and price_per_hour
            if booking.mark_as_paid(razorpay_payment_id=payment_id):
                db.session.commit()
                current_app.logger.info(f"handle_payment: Payment successful and booking {booking.id} updated.")
                # Return success JSON for AJAX handler
                # Assuming called by frontend JS after Razorpay popup closes
                return jsonify({
                    'success': True,
                    'message': 'Payment successful! Your booking is confirmed.',
                    'redirect_url': url_for('booking.booking_detail', booking_id=booking.id)
                })
            else:
                db.session.rollback()
                current_app.logger.error(
                    f"handle_payment: Failed to mark booking {booking.id} as paid after verification.")
                return jsonify(
                    {'success': False, 'message': 'Failed to update booking status after payment verification.'}), 500
            # --- END CRITICAL FIX 8 ---

        else:
            # Payment signature verification failed
            current_app.logger.warning(f"handle_payment: Payment verification explicitly failed for order {order_id}")
            return jsonify({'success': False, 'message': 'Payment verification failed.'}), 400

    # --- CRITICAL FIX 9: Specific Razorpay signature error handling ---
    # AFTER (Corrected - Moved specific handling inside main try block)
    # The specific SignatureVerificationError is now caught by the inner try-except
    # Only catch general exceptions here for truly unexpected issues
    except Exception as e:
        # Handle other unexpected errors (network issues, JSON parsing, etc.)
        db.session.rollback()
        current_app.logger.exception(f"Unexpected error in handle_payment: {e}")
        return jsonify({'success': False,
                        'message': 'An unexpected error occurred during payment processing. Please try again or contact support.'}), 500

    # --- END CRITICAL FIX 9 ---


# --- End Payment Handler ---    # --- End Payment Handler ---
# --- End Route Definitions ---
@booking_bp.route('/my-bookings')  # This creates endpoint 'booking.my_bookings'
@login_required
def my_bookings():
    """
    Display the current user's bookings.
    This is the 'booking.my_bookings' endpoint.
    Could be an alias for list_bookings or have specific logic.
    """
    # This could simply delegate to list_bookings
    # return list_bookings() # If list_bookings is a callable function

    # Or implement specific logic here
    bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.created_at.desc()).all()
    return render_template('user/bookings/list.html', bookings=bookings)  # Use appropriate template


# routes/booking.py (Add this new route at the end)
# ... (existing imports and routes) ...


@booking_bp.route('/bookings/<int:booking_id>/cancel', methods=['POST'])
@login_required
def cancel_booking(booking_id):
    """
    Cancel a booking by the user.
    This is the 'booking.cancel_booking' endpoint.
    """
    booking = Booking.query.get_or_404(booking_id)

    # Check if user owns this booking
    if booking.user_id != current_user.id:
        flash('Access denied.')
        return redirect(url_for('car.home'))

    # Check if booking can be cancelled by user
    if not booking.can_be_cancelled_by_user():
        flash('This booking cannot be cancelled at this time.', 'warning')
        return redirect(url_for('booking.booking_detail', booking_id=booking_id))

    # Get reason from form
    reason = request.form.get('reason', '').strip()
    if reason == 'Other':
        reason = request.form.get('other_reason', '').strip()

    if not reason:
        flash('Please provide a reason for cancellation.', 'danger')
        return redirect(url_for('booking.booking_detail', booking_id=booking_id))

    # Attempt to cancel
    try:
        if booking.cancel_by_user(reason):
            db.session.commit()
            flash(
                f'Booking #{booking.id} cancelled successfully. A refund of ₹{booking.refund_amount:.2f} will be processed.',
                'success')
        else:
            flash('Failed to cancel booking.', 'danger')
    except Exception as e:
        db.session.rollback()
        print(f"Error cancelling booking: {e}")
        flash('An error occurred while cancelling the booking.', 'danger')

    return redirect(url_for('booking.booking_detail', booking_id=booking_id))

# ... (rest of routes/booking.py) ...

def get_min_extension_date(self):
    """Returns the earliest possible date for an extension (1 day after end)."""
    return self.end_date + timedelta(days=1)
