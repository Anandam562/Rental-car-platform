from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from . import host_bp
from models import db
from models.host import Host
from models.car import Car
from models.booking import Booking


@host_bp.route('/')
@login_required
def dashboard():
    """Host dashboard overview"""
    # --- CRITICAL FIX 1: Correct Host Lookup and Authorization ---
    # Fetch the host profile associated with the current user
    host = Host.query.filter_by(user_id=current_user.id).first()

    # Check if the host profile exists
    if not host:
        flash('Please complete your host profile first.', 'warning') # Use 'warning' category
        # Redirect to the host profile setup page
        # Make sure 'host.setup_profile' is the correct endpoint name for your profile setup route
        return redirect(url_for('host.setup_profile')) # Adjust endpoint name if needed
    # --- END CRITICAL FIX 1 ---

    # --- Fetch Host Statistics ---
    # 1. Total Cars Listed
    total_cars = Car.query.filter_by(host_id=host.id).count()

    # 2. Pending Booking Approvals
    # Join Booking with Car to link bookings to the host's cars
    # Filter for bookings with status 'pending' for the host's cars
    pending_approvals = Booking.query.join(Car).filter(
        Car.host_id == host.id,
        Booking.status == 'pending' # Use status field
    ).count()

    # 3. Active Bookings
    # Filter for bookings with status 'active' for the host's cars
    # --- CRITICAL FIX 2: Use 'status' field instead of non-existent 'is_active' ---
    active_bookings = Booking.query.join(Car).filter(
        Car.host_id == host.id,
        Booking.status == 'active' # Use status field to find active bookings
    ).count()
    # --- END CRITICAL FIX 2 ---

    # 4. Total Earnings (from host's wallet balance)
    total_earnings = host.wallet_balance # Assumes wallet_balance is updated correctly on the Host model

    # 5. Recent Pending Bookings (last 5)
    pending_bookings = Booking.query.join(Car).filter(
        Car.host_id == host.id,
        Booking.status == 'pending' # Filter for pending status
    ).order_by(Booking.created_at.desc()).limit(5).all()
    # --- End Fetch Statistics ---

    # --- Prepare Context for Template ---
    context = {
        'host': host,
        'total_cars': total_cars,
        'pending_approvals': pending_approvals,
        'active_bookings': active_bookings,
        'total_earnings': total_earnings,
        'pending_bookings': pending_bookings
    }
    # --- End Context ---

    # --- Render Template ---
    return render_template('host/dashboard.html', **context)
    # --- End Render ---
# --- End Dashboard Route ---


@host_bp.route('/bookings/<int:booking_id>/approve', methods=['POST'])
@login_required
def approve_booking(booking_id):
    """Approve a booking"""
    host = Host.query.filter_by(user_id=current_user.id).first()
    booking = Booking.query.get_or_404(booking_id)

    # Check if host owns this car
    if booking.car.host_id != host.id:
        flash('Access denied')
        return redirect(url_for('host.dashboard'))

    # Check if booking can be approved
    if not booking.can_be_approved():
        flash('This booking cannot be approved')
        return redirect(url_for('host.dashboard'))

    # Approve booking
    booking.host_approval = True
    booking.status = 'approved'
    db.session.commit()

    flash('Booking approved successfully!')
    return redirect(url_for('host.dashboard'))