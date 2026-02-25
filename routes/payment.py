# routes/payment.py
import os  # <-- Import os at the top
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
import razorpay
import hmac
import hashlib
from datetime import datetime
from models import db
from models.booking import Booking

# from models.car import Car # If needed

payment_bp = Blueprint('payment', __name__)

# --- CRITICAL FIX: Move Razorpay client initialization ---
# BEFORE (Incorrect - Module level access to current_app)
# RAZORPAY_KEY_ID = current_app.config.get('RAZORPAY_KEY_ID')
# RAZORPAY_KEY_SECRET = current_app.config.get('RAZORPAY_KEY_SECRET')
# AFTER (Correct - Use os.getenv or access within app context)
# Option 1: Use os.getenv (recommended for keys that don't change)
RAZORPAY_KEY_ID = os.getenv('RAZORPAY_KEY_ID')  # Get from environment variables
RAZORPAY_KEY_SECRET = os.getenv('RAZORPAY_KEY_SECRET')  # Get from environment variables

# Initialize client only if keys are present
if RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET:
    try:
        razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
        razorpay_client.set_app_details({"title": "ZoomCarClone", "version": "1.0"})
    except Exception as e:
        print(f"Error initializing Razorpay client: {e}")
        razorpay_client = None
else:
    print("Razorpay keys not found in environment variables (.env file).")
    razorpay_client = None


# --- END CRITICAL FIX ---

@payment_bp.route('/initiate/<int:booking_id>')
@login_required
def initiate_payment(booking_id):
    """Initiate Razorpay payment for a booking."""
    booking = Booking.query.get_or_404(booking_id)

    # Authorization check
    if booking.user_id != current_user.id:
        flash('Access denied.')
        return redirect(url_for('car.home'))

    # Check if booking can be paid
    if not booking.can_be_paid():
        flash('This booking cannot be paid at this time.')
        return redirect(url_for('user.booking_detail', booking_id=booking_id))  # Assuming user blueprint

    # --- Razorpay Integration ---
    if not razorpay_client:
        flash('Payment gateway is currently unavailable. Please try again later.', 'danger')
        return redirect(url_for('user.booking_detail', booking_id=booking_id))  # Assuming user blueprint

    try:
        # Create a Razorpay Order
        order_data = {
            'amount': int(booking.total_price * 100),  # Razorpay expects amount in paise
            'currency': 'INR',
            'receipt': f"booking_receipt_{booking.id}",
            'payment_capture': 1  # Auto-capture payment
        }
        razorpay_order = razorpay_client.order.create(order_data)
        razorpay_order_id = razorpay_order['id']

        # Store order ID in booking
        booking.razorpay_order_id = razorpay_order_id
        db.session.commit()

        # Prepare context for template
        context = {
            'booking': booking,
            'razorpay_key_id': RAZORPAY_KEY_ID,
            'razorpay_order_id': razorpay_order_id,
            'total_amount_paise': int(booking.total_price * 100),
            'total_amount_rupees': booking.total_price
        }

        return render_template('payment/checkout.html', **context)

    except razorpay.errors.RazorpayError as e:
        print(f"Razorpay API error: {e}")
        flash('Failed to initiate payment. Please try again.', 'danger')
        return redirect(url_for('user.booking_detail', booking_id=booking_id))  # Assuming user blueprint
    except Exception as e:
        print(f"Unexpected error in initiate_payment: {e}")
        flash('An unexpected error occurred. Please try again.', 'danger')
        return redirect(url_for('user.booking_detail', booking_id=booking_id))  # Assuming user blueprint
    # --- End Razorpay Integration ---


@payment_bp.route('/handler', methods=['POST'])
@login_required
def handle_payment():
    """Handle Razorpay payment callback/verification."""
    if not razorpay_client:
        flash('Payment gateway is currently unavailable.', 'danger')
        # Redirect to appropriate place (user dashboard?)
        return redirect(url_for('car.home'))  # Or user dashboard

    try:
        # Get payment details from Razorpay callback
        payment_id = request.form.get('razorpay_payment_id')
        order_id = request.form.get('razorpay_order_id')
        signature = request.form.get('razorpay_signature')

        if not payment_id or not order_id or not signature:
            flash('Invalid payment data received.', 'danger')
            return redirect(url_for('car.home'))  # Or user dashboard

        # Verify the payment signature
        params_dict = {
            'razorpay_order_id': order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        }

        result = razorpay_client.utility.verify_payment_signature(params_dict)

        if result:
            # Payment signature verified successfully
            # Find the booking associated with this order
            booking = Booking.query.filter_by(razorpay_order_id=order_id).first()
            if not booking or booking.user_id != current_user.id:
                flash('Booking not found or access denied.', 'danger')
                return redirect(url_for('car.home'))  # Or user dashboard

            if booking.payment_status == 'completed':
                flash('Payment already processed for this booking.', 'info')
                # Redirect to booking detail or user dashboard
                return redirect(url_for('user.booking_detail', booking_id=booking.id))  # Assuming user blueprint

            # --- CRITICAL: Update booking status ---
            booking.payment_status = 'completed'
            booking.payment_date = datetime.utcnow()
            booking.razorpay_payment_id = payment_id  # Store payment ID
            # Update booking status to 'paid' or 'active' depending on your flow
            booking.status = 'paid'  # Or 'active' if trip starts immediately after payment

            # --- CRITICAL: Update Host Wallet ---
            # Assuming Host model has add_to_wallet method and a relationship to Car
            # This assumes Car has a 'host' relationship
            host = booking.car.host  # Access host via car relationship
            if host:
                # Example: Add 90% of total price to host's wallet
                host_earning = booking.total_price * 0.9
                host.add_to_wallet(host_earning)
                # You might want to record this in a WalletTransaction model
            # --- END CRITICAL ---

            db.session.commit()

            flash('Payment successful! Your booking is confirmed.', 'success')
            # Redirect to booking detail page
            return redirect(url_for('user.booking_detail', booking_id=booking.id))  # Assuming user blueprint
        else:
            # Payment signature verification failed
            flash('Payment verification failed. Please contact support.', 'danger')
            print(f"Razorpay signature verification failed for order {order_id}")
            return redirect(url_for('car.home'))  # Or user dashboard

    except razorpay.errors.SignatureVerificationError as e:
        # Specific Razorpay signature error
        flash(f"Payment verification failed: {str(e)}", "danger")
        print(f"SignatureVerificationError: {e}")
        return redirect(url_for('car.home'))  # Or user dashboard
    except Exception as e:
        # Handle other unexpected errors
        db.session.rollback()  # Rollback on error
        print(f"Unexpected error in handle_payment: {e}")
        flash("An error occurred during payment processing. Please contact support.", "danger")
        return redirect(url_for('car.home'))  # Or user dashboard

# Register blueprint in app.py
# app.register_blueprint(payment_bp, url_prefix='/payment')
