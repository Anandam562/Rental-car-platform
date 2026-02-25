# routes/user/dashboard.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from . import user_bp
from models import db
from models.booking import Booking
from datetime import datetime
import pytz # Import pytz for timezone handling

@user_bp.route('/dashboard') # This route combined with url_prefix='/user' makes the full URL /user/dashboard
@login_required
def dashboard():
    """
    Display the user dashboard with upcoming trips.
    This is the 'user.dashboard' endpoint.
    """
    # --- Fetch Upcoming Bookings ---
    # Filter bookings where:
    # 1. The booking belongs to the current user
    # 2. The status indicates it's pending, approved, or paid (not cancelled/completed)
    # 3. The start date is in the future OR the trip is currently active
    now_utc = datetime.utcnow() # Get current time in UTC
    upcoming_bookings = Booking.query.filter(
        Booking.user_id == current_user.id,
        Booking.status.in_(['pending', 'approved', 'paid', 'active']), # Adjust statuses as needed
        Booking.start_date >= now_utc # Trip starts now or in the future, OR is active
    ).order_by(Booking.start_date.asc()).all() # Order by start date ascending (soonest first)
    # --- End Fetch Upcoming Bookings ---

    # --- Process Bookings for Template ---
    # Prepare a list of tuples (or dictionaries) containing booking and related data for the template
    processed_bookings = []
    for booking in upcoming_bookings:
        time_to_start = booking.start_date - now_utc
        # Check if within 1 hour to enable button (and status allows starting)
        enable_start_button = (
            time_to_start.total_seconds() <= (1 * 60 * 60) and # 1 hour in seconds
            time_to_start.total_seconds() > 0 and # Not already started
            booking.status in ['paid', 'approved'] # Check status
        )
        processed_bookings.append({
            'booking': booking,
            'time_to_start': time_to_start,
            'enable_start_button': enable_start_button
        })
    # --- End Process Bookings for Template ---

    # --- Fetch Wallet Data (Keep existing logic or adapt as needed) ---
    # Wallet balance is directly on the User object
    wallet_balance = current_user.wallet_balance

    # Fetch recent wallet transactions (Keep existing logic or adapt as needed)
    # For simplicity, using the direct query approach again
    from models.wallet_transaction import WalletTransaction
    recent_transactions = WalletTransaction.query.filter_by(
        user_id=current_user.id
    ).order_by(
        WalletTransaction.timestamp.desc()
    ).limit(5).all()
    # --- End Fetch Wallet Data ---

    # --- CRITICAL FIX: Get Server Time in IST ---
    # Get the current UTC time
    utc_now = datetime.utcnow()
    # Define UTC and IST timezones
    utc_tz = pytz.utc
    ist_tz = pytz.timezone('Asia/Kolkata') # Indian Standard Time
    # Localize the UTC datetime to UTC timezone (attach timezone info)
    utc_now_with_tz = utc_tz.localize(utc_now)
    # Convert the localized UTC time to IST
    ist_now = utc_now_with_tz.astimezone(ist_tz)
    # --- END CRITICAL FIX ---

    # --- Prepare Context for Template ---
    context = {
        'user': current_user,
        'upcoming_bookings': processed_bookings, # Pass the processed list
        'wallet_balance': wallet_balance,
        'recent_transactions': recent_transactions,
        # --- CRITICAL FIX: Pass IST time to template ---
        'server_time': ist_now # Pass the IST datetime object
        # --- END CRITICAL FIX ---
    }
    # --- End Context ---

    # --- Render Template ---
    return render_template('user/dashboard.html', **context)
    # --- End Render ---