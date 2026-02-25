# routes/user/bookings.py
import razorpay
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user

from forms.user import StartTripForm
from models import db
from models.booking import Booking
from models.host_feedback import HostFeedback
from models.host_rating import HostRating
from models.photo import Photo # Import the Photo model
from werkzeug.utils import secure_filename
import os
import json

from models.wallet_transaction import WalletTransaction
# Import user_bp from the package's __init__.py
from routes.user import user_bp

RAZORPAY_KEY_ID = os.getenv('RAZORPAY_KEY_ID')
RAZORPAY_KEY_SECRET = os.getenv('RAZORPAY_KEY_SECRET')
if RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET:
    try:
        razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
        razorpay_client.set_app_details({"title": "ZoomCarClone", "version": "1.0"})
    except Exception as e:
        current_app.logger.error(f"Error initializing Razorpay client in user/bookings: {e}")
        razorpay_client = None
else:
    current_app.logger.warning("Razorpay keys not found in environment variables (user/bookings).")
    razorpay_client = None
# - End Razorpay Client Initialization -


# --- List Bookings ---
# @user_bp.route('/bookings') # This creates endpoint 'user.list_bookings'
# @login_required
# def list_bookings():
#     """List the current user's bookings."""
#     bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.created_at.desc()).all()
#     return render_template('user/bookings/list.html', bookings=bookings)

@user_bp.route('/bookings') # This creates endpoint 'user.list_bookings'
@login_required
def list_bookings():
    """List the current user's bookings.
    This is the 'user.list_bookings' endpoint.
    """
    # --- Fetch User Bookings ---
    # Filter bookings where:
    # 1. The booking belongs to the current user
    # 2. The status indicates it's relevant (adjust as needed)
    # For simplicity, fetching all bookings for the user
    bookings = Booking.query.filter_by(
        user_id=current_user.id
        # Add status filter if needed, e.g.,
        # status.in_(['pending', 'approved', 'paid', 'active', 'completed', 'cancelled'])
    ).order_by(
        Booking.created_at.desc() # Order by creation date descending (newest first)
    ).all()
    # --- End Fetch User Bookings ---

    # --- CRITICAL FIX: Fetch Wallet Data ---
    # Wallet balance is directly on the User object (assuming it's a column or property)
    wallet_balance = current_user.wallet_balance

    # Fetch recent wallet transactions (optional, adjust limit as needed)
    # For simplicity, using the direct query approach again
    from models.wallet_transaction import WalletTransaction
    recent_transactions = WalletTransaction.query.filter_by(
        user_id=current_user.id
    ).order_by(
        WalletTransaction.timestamp.desc()
    ).limit(5).all()
    # --- END CRITICAL FIX ---

    # --- Prepare Context for Template ---
    context = {
        'user': current_user, # Pass current user object (often needed by base template)
        'bookings': bookings, # Pass the fetched bookings list
        # --- CRITICAL FIX: Pass Wallet Data to Template Context ---
        'wallet_balance': wallet_balance, # Pass the wallet balance
        'recent_transactions': recent_transactions # Pass recent transactions
        # --- END CRITICAL FIX ---
    }
    # --- End Context ---

    # --- Render Template ---
    # Pass the context dictionary containing 'bookings', 'wallet_balance', and 'recent_transactions'
    return render_template('user/bookings/list.html', **context)
    # --- End Render ---
# --- End List Bookings Route ---

# --- Booking Detail ---
@user_bp.route('/bookings/<int:booking_id>') # This creates endpoint 'user.booking_detail'
@login_required
def booking_detail(booking_id):
    """View detailed information for a specific booking."""
    booking = Booking.query.get_or_404(booking_id)

    # Authorization check
    if booking.user_id != current_user.id:
        flash('Access denied.')
        return redirect(url_for('car.home'))

    # Calculate min_extension_date (if needed for extensions, which are separate logic now)
    # min_extension_date = booking.get_min_extension_date() # Not used in new flow, but kept if extensions are still a feature elsewhere

    return render_template(
        'user/bookings/detail.html',
        booking=booking,
        # min_extension_date=min_extension_date # Pass if extensions are still used here
    )

# --- NEW: Trip Activation (Pickup Photos) ---
# --- NEW: Trip Activation (Pickup Photos) ---
# --- CRITICAL FIX: Ensure start_trip route uses the model method ---
@user_bp.route('/bookings/<int:booking_id>/start_trip', methods=['GET', 'POST'])
@login_required
def start_trip(booking_id):
    """
    Handle pickup photo upload and trip activation using WTForms.
    This is the 'user.start_trip' endpoint.
    """
    # --- Fetch Booking ---
    booking = Booking.query.get_or_404(booking_id)
    # --- End Fetch Booking ---

    # --- Authorization Check ---
    if booking.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('car.home')) # Or redirect to a more appropriate page
    # --- End Authorization ---

    # --- Check if booking can be activated ---
    # Use the model method to ensure consistency
    if not booking.can_be_activated_by_user():
        flash('Trip cannot be started at this time.', 'warning')
        # Redirect back to the booking detail page for context
        return redirect(url_for('user.booking_detail', booking_id=booking.id))
    # --- End Check ---

    # --- CRITICAL FIX 2: Instantiate the StartTripForm ---
    # Pass the booking object to the form if needed for future custom validation
    form = StartTripForm(booking_obj=booking) # Create an instance of the form
    # --- END CRITICAL FIX 2 ---

    if request.method == 'POST':
        # --- CRITICAL FIX 3: Use WTForms Validation ---
        # First, check if the form (including CSRF) is valid
        if form.validate_on_submit(): # This checks CSRF token and FileAllowed validator
            # --- Handle POST: Process Uploaded Photos ---
            # Get the list of files directly from the request object
            # This is the standard and reliable way to get multiple files
            files = request.files.getlist('pickup_photos') # 'pickup_photos' is the name attribute of the input

            # --- CRITICAL FIX 4: Validate Number of Files (Server-Side) ---
            # Perform validation on the number of files selected
            # This is where the route-based validation (mentioned in the form class) happens.
            if len(files) > 10 or len(files) == 0: # Assuming max 10 photos, at least 1 required
                flash('Please select between 1 and 10 photos.', 'danger')
                # Re-render the template with the form (now defined) and booking
                # Pass any error context if needed
                return render_template('user/bookings/start_trip.html', booking=booking, form=form)
            # --- END CRITICAL FIX 4 ---

            uploaded_photo_records = [] # List to hold Photo model instances

            # Save files and create Photo records
            for file in files:
                # Check if a file was actually selected (browsers might send empty entries)
                if file and file.filename != '':
                    try:
                        filename = secure_filename(file.filename)
                        # Add booking ID to filename for uniqueness
                        name, ext = os.path.splitext(filename)
                        # Format: pickup_<booking_id>_<original_name><extension>
                        filename = f"pickup_{booking.id}_{name}{ext}"
                        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                        file.save(filepath)

                        # Create Photo record in the database
                        photo = Photo(
                            booking_id=booking.id,
                            filename=filename,
                            photo_type='pickup' # Specify the type
                        )
                        db.session.add(photo)
                        uploaded_photo_records.append(photo) # Store for potential use

                    except Exception as e:
                        current_app.logger.error(f"Error saving pickup photo: {e}")
                        flash('An error occurred while saving photos. Please try again.', 'danger')
                        db.session.rollback() # Rollback on error
                        # Optionally, delete any files saved so far if partial save is undesirable
                        return render_template('user/bookings/start_trip.html', booking=booking, form=form) # Re-render with form

            # --- Activate the Trip ---
            # Call the model method to handle status changes
            if booking.activate_trip(): # This should now work with the updated logic
                try:
                    db.session.commit() # Commit both photo saves and booking activation
                    flash('Trip started successfully! Photos uploaded.', 'success')
                    # Redirect to booking detail page
                    return redirect(url_for('user.booking_detail', booking_id=booking.id))
                except Exception as e:
                    db.session.rollback()
                    current_app.logger.error(f"Error activating booking {booking.id}: {e}")
                    flash('Failed to start trip after uploading photos. Please try again.', 'danger')
                    # Optionally, delete saved files if DB commit fails
                    return render_template('user/bookings/start_trip.html', booking=booking, form=form) # Re-render with form
            else:
                db.session.rollback()
                flash('Failed to start trip. Please ensure the trip is eligible to start.', 'danger')
                return render_template('user/bookings/start_trip.html', booking=booking, form=form) # Re-render with form
            # --- End Activate Trip ---
        else:
            # If WTForms validation fails (e.g., CSRF error, file type error)
            # form.validate_on_submit() will automatically populate form.errors
            # The template will display these errors.
            # Log specific errors if needed
            # for fieldName, errorMessages in form.errors.items():
            #     current_app.logger.debug(f"Form field '{fieldName}' has errors: {errorMessages}")
            flash('Please correct the errors below and try again.', 'danger')
            # Re-render the template with the form (containing errors) and booking
            return render_template('user/bookings/start_trip.html', booking=booking, form=form)
        # --- END CRITICAL FIX 3 ---

    # GET request: Show the upload form
    # --- CRITICAL FIX 5: Pass the form instance to the template ---
    return render_template('user/bookings/start_trip.html', booking=booking, form=form)
    # --- END CRITICAL FIX 5 ---


# --- NEW: Trip Completion (Dropoff Photos) ---
@user_bp.route('/bookings/<int:booking_id>/complete_trip', methods=['GET', 'POST'])
@login_required
def complete_trip(booking_id):
    """Handle optional dropoff photo upload and trip completion."""
    booking = Booking.query.get_or_404(booking_id)

    # Authorization check
    if booking.user_id != current_user.id:
        flash('Access denied.')
        return redirect(url_for('car.home'))

    # Check if booking can be completed
    if not booking.can_be_completed_by_user():
        flash('Trip cannot be completed at this time.')
        return redirect(url_for('user.booking_detail', booking_id=booking.id))

    if request.method == 'POST':
        files = request.files.getlist('dropoff_photos')
        uploaded_photo_filenames = []

        # Validate and save photos (optional)
        if len(files) > 10:
            flash('Maximum of 10 photos allowed for dropoff.')
            return render_template('user/bookings/complete_trip.html', booking=booking)

        for file in files:
            if file and file.filename != '':
                try:
                    filename = secure_filename(file.filename)
                    # Add booking ID to filename for uniqueness
                    name, ext = os.path.splitext(filename)
                    filename = f"dropoff_{booking.id}_{name}{ext}"
                    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)

                    # Create Photo record
                    photo = Photo(
                        booking_id=booking.id,
                        filename=filename,
                        photo_type='dropoff' # Set type to 'dropoff'
                    )
                    db.session.add(photo)
                    uploaded_photo_filenames.append(filename) # Store for potential use
                except Exception as e:
                    current_app.logger.error(f"Error saving dropoff photo: {e}")
                    flash('An error occurred while saving photos. Please try again.')
                    db.session.rollback() # Rollback on error
                    return render_template('user/bookings/complete_trip.html', booking=booking)
        # --- CRITICAL FIX: Complete the Trip ---
        # Call the model method to handle completion logic
        # This ensures consistency with the logic defined in the Booking model
        # The total_price used here is already calculated based on hours and price_per_hour
        if booking.complete_trip():  # This changes status to 'completed', is_active=False, is_completed=True
            db.session.commit()
            flash('Trip completed successfully! Photos uploaded.', 'success')
            # --- CRITICAL FIX: Check Feedback Eligibility AFTER Completion ---
            # After successful completion, check if user can give feedback
            # This ensures the booking status is updated before checking eligibility
            if booking.can_give_feedback():  # This checks status='completed' and is_completed=True
                # Redirect to the give feedback page
                return redirect(url_for('user.give_feedback', booking_id=booking.id))
            else:
                # If feedback cannot be given (e.g., already given), redirect to booking detail
                return redirect(url_for('user.booking_detail', booking_id=booking.id))
        else:
            db.session.rollback()
            flash('Failed to complete trip. Please try again.')
            return render_template('user/bookings/complete_trip.html', booking=booking)
        # --- END CRITICAL FIX ---
        # --- End Complete Trip ---
    # GET request: Show the upload form (optional photos)
    return render_template('user/bookings/complete_trip.html', booking=booking)

# --- CRITICAL FIX: Ensure Cancel Booking Route is Defined ---
@user_bp.route('/bookings/<int:booking_id>/cancel', methods=['POST'])
@login_required
def cancel_booking(booking_id):
    """Cancel a booking by the user."""
    booking = Booking.query.get_or_404(booking_id)

    # Authorization check
    if booking.user_id != current_user.id:
        flash('Access denied.')
        return redirect(url_for('car.home'))

    # Check if booking can be cancelled by user
    if not booking.can_be_cancelled_by_user():
        flash('This booking cannot be cancelled at this time.', 'warning')
        return redirect(url_for('user.booking_detail', booking_id=booking_id))

    # Get reason from form
    reason = request.form.get('reason', '').strip()
    if reason == 'Other':
        reason = request.form.get('other_reason', '').strip()

    if not reason:
        flash('Please provide a reason for cancellation.', 'danger')
        return redirect(url_for('user.booking_detail', booking_id=booking_id))

    # Attempt to cancel
    try:
        if booking.cancel_by_user(reason):
            db.session.commit()
            flash(
                f'Booking #{booking.id} cancelled successfully. A refund of ₹{booking.refund_amount:.2f} will be processed.',
                'success')

            # --- CRITICAL FIX: Send Notification to User ---
            from utils.notification_sender import send_notification_to_user
            send_notification_to_user(
                user_id=booking.user_id,
                message=f'Your booking #{booking.id} for {booking.car.make} {booking.car.model} has been cancelled. Reason: {reason[:50]}...'
            )
            # --- END CRITICAL FIX ---

            # --- CRITICAL FIX: Send Notification to Host ---
            from utils.notification_sender import send_notification_to_host
            send_notification_to_host(
                host_user_id=booking.car.host.user_id,
                message=f'A booking #{booking.id} for your {booking.car.make} {booking.car.model} has been cancelled by the user. Reason: {reason[:50]}...'
            )
            # --- END CRITICAL FIX ---

        else:
            flash('Failed to cancel booking.', 'danger')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error cancelling booking: {e}")
        flash('An error occurred while cancelling the booking.', 'danger')

    return redirect(url_for('user.booking_detail', booking_id=booking_id))
# --- END CRITICAL FIX ---

# --- NEW: Pay for Booking (User Initiated) ---
@user_bp.route('/bookings/<int:booking_id>/pay', methods=['GET'])
@login_required
def pay_booking(booking_id):
    """
    Initiate Razorpay payment for a specific booking.
    This is the 'user.pay_booking' endpoint.
    """
    booking = Booking.query.get_or_404(booking_id)

    # - Authorization Check -
    if booking.user_id != current_user.id:
        flash('Access denied.')
        return redirect(url_for('car.home'))
    # - End Authorization -

    # - Check if Booking can be Paid -
    if not booking.can_be_paid(): # Assuming you have this method in Booking model
        flash('This booking cannot be paid at this time.')
        return redirect(url_for('user.booking_detail', booking_id=booking_id))
    # - End Check -

    # - Razorpay Integration -
    if not razorpay_client:
        flash('Payment gateway is currently unavailable. Please try again later.', 'danger')
        return redirect(url_for('user.booking_detail', booking_id=booking_id))

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

        # Store order ID in booking and commit
        booking.razorpay_order_id = razorpay_order_id
        db.session.commit() # Crucial: Save the order ID before rendering checkout

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
        return render_template('user/bookings/razorpay_checkout.html', **context)

    # - CRITICAL FIX: Catch the correct Razorpay exception -
    except razorpay.errors.BadRequestError as e: # Catch specific known errors or general Exception
        print(f"Razorpay API error (BadRequest): {e}")
        flash(f'Failed to initiate payment: {str(e)}', 'danger')
        return redirect(url_for('user.booking_detail', booking_id=booking_id))
    except Exception as e: # Catch any other unexpected errors from Razorpay SDK
        db.session.rollback()
        print(f"Unexpected error in user.pay_booking: {e}")
        flash('An unexpected error occurred during payment processing. Please try again.', 'danger')
        return redirect(url_for('user.booking_detail', booking_id=booking_id))
    # - END CRITICAL FIX -
    # - End Razorpay Integration -

# --- END NEW: Pay for Booking ---

# --- NEW: Give Feedback Route ---
# --- CRITICAL FIX: Ensure Give Feedback Route is Defined ---
@user_bp.route('/bookings/<int:booking_id>/feedback', methods=['GET', 'POST'])
@login_required
def give_feedback(booking_id):
    """Allow user to give feedback and rating for a completed booking."""
    booking = Booking.query.get_or_404(booking_id)

    # Authorization check
    if booking.user_id != current_user.id:
        flash('Access denied.')
        return redirect(url_for('car.home'))

    # Check if feedback can be given
    if not booking.can_give_feedback():
        flash('Feedback cannot be given for this booking at this time.', 'warning')
        return redirect(url_for('user.booking_detail', booking_id=booking_id))

    if request.method == 'POST':
        rating_str = request.form.get('rating')
        feedback_text = request.form.get('feedback', '').strip()

        # Validate rating
        try:
            rating = int(rating_str)
            if rating < 1 or rating > 5:
                raise ValueError("Rating out of range")
        except (ValueError, TypeError):
            flash('Please select a valid rating (1-5 stars).', 'danger')
            return render_template('user/bookings/give_feedback.html', booking=booking)

        # Validate feedback text (optional, but good practice)
        if not feedback_text:
            flash('Please provide feedback text.', 'danger')
            return render_template('user/bookings/give_feedback.html', booking=booking)

        try:
            # Create Host Rating Record
            host_rating = HostRating(
                host_id=booking.car.host.id,
                user_id=current_user.id,
                booking_id=booking.id,
                rating=rating,
                comment=feedback_text[:255]
            )
            db.session.add(host_rating)

            # Create Host Feedback Record
            host_feedback = HostFeedback(
                host_id=booking.car.host.id,
                user_id=current_user.id,
                booking_id=booking.id,
                subject=f"Feedback for Booking #{booking.id}",
                message=feedback_text[:500],
                is_resolved=False
            )
            db.session.add(host_feedback)

            db.session.commit()
            flash('Thank you for your feedback and rating!', 'success')

            # --- CRITICAL FIX: Send Notification to Host ---
            from utils.notification_sender import send_notification_to_host
            send_notification_to_host(
                host_user_id=booking.car.host.user_id,
                message=f"You have received new feedback and a {rating}-star rating for Booking #{booking.id}."
            )
            # --- END CRITICAL FIX ---

            return redirect(url_for('user.booking_detail', booking_id=booking_id))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error submitting feedback for booking {booking_id}: {e}")
            flash('An error occurred while submitting your feedback. Please try again.', 'danger')
            return render_template('user/bookings/give_feedback.html', booking=booking)

    # GET request: Show the feedback form
    return render_template('user/bookings/give_feedback.html', booking=booking)
# --- END CRITICAL FIX ---

# routes/user/bookings.py (Inside the withdraw_funds function)
# ... (previous imports and route definition) ...

@user_bp.route('/wallet/withdraw', methods=['GET', 'POST'])
@login_required
def withdraw_funds():
    """
    Placeholder for withdrawing funds from the user's wallet.
    This is the 'user.withdraw_funds' endpoint.
    Implement logic for withdrawal requests and processing.
    """
    if request.method == 'POST':
        # --- Handle POST: Process Withdrawal Request ---
        amount_str = request.form.get('amount')
        try:
            amount = float(amount_str)
            if amount <= 0:
                flash('Amount must be greater than zero.', 'danger')
                return render_template('user/wallet/withdraw.html')

            # --- Check Wallet Balance ---
            if current_user.wallet_balance < amount:
                flash('Insufficient funds in your wallet.', 'danger')
                return render_template('user/wallet/withdraw.html')
            # --- END Check Wallet Balance ---

            # --- CRITICAL FIX: Implement Withdrawal Logic ---
            # This could involve:
            # 1. Validating the amount against minimum/maximum limits.
            # 2. Checking user's KYC status or linked bank accounts.
            # 3. Creating a withdrawal request record in the database.
            # 4. Initiating an external transfer via a payment gateway or bank API.
            # 5. Updating the user's wallet balance and recording the transaction.
            # For now, simulate a successful withdrawal
            flash(f'Withdrawal of ₹{amount:.2f} initiated. Integration with payment/banking system required.', 'info')
            # Simulate deducting from wallet and recording transaction
            if current_user.deduct_from_wallet(amount):
                # Record the withdrawal transaction
                WalletTransaction.record_withdrawal(
                    user=current_user,
                    amount=amount,
                    withdrawal_reference="Simulated Withdrawal" # Add actual reference
                )
                db.session.commit()
                flash(f'Simulated withdrawal of ₹{amount:.2f} successful!', 'success')
            else:
                db.session.rollback()
                flash('Failed to simulate withdrawal.', 'danger')
            # --- END CRITICAL FIX ---

        except ValueError:
            flash('Invalid amount entered.', 'danger')
        except Exception as e:
            db.session.rollback()
            # --- CRITICAL FIX: Use current_app.logger instead of app.logger ---
            # BEFORE (Incorrect - 'app' is not defined in this scope)
            # app.logger.error(f"Error processing withdrawal: {e}")
            # AFTER (Corrected - Use current_app.logger)
            current_app.logger.error(f"Error processing withdrawal: {e}") # <-- CORRECTED LINE
            # --- END CRITICAL FIX ---
            flash('An error occurred while processing your withdrawal. Please try again.', 'danger')

        return render_template('user/wallet/withdraw.html')
    # --- END Handle POST ---

    # GET request: Show the withdrawal form
    return render_template('user/wallet/withdraw.html')
# --- END PLACEHOLDER: Withdraw Funds Route ---

