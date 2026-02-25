# routes/host/bookings.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from . import host_bp
from models import db
from models.host import Host
from models.booking import Booking


# ... (existing imports and routes like dashboard, list_bookings, booking_detail) ...

@host_bp.route('/bookings/<int:booking_id>/extension/approve', methods=['POST'])
@login_required
def approve_extension(booking_id):
    """
    Approve a user's extension request for a booking.
    This is the 'host.approve_extension' endpoint.
    """
    host = Host.query.filter_by(user_id=current_user.id).first_or_404()
    booking = Booking.query.get_or_404(booking_id)

    # Check if host owns the car for this booking
    if booking.car.host_id != host.id:
        flash('Access denied.')
        return redirect(url_for('host.dashboard'))

    # Check if extension can be approved
    if not booking.can_approve_extension(host):
        flash('This extension request cannot be approved.', 'warning')
        return redirect(url_for('host.booking_detail', booking_id=booking_id))

    # Attempt to approve
    success, message = booking.approve_extension(host)
    if success:
        db.session.commit()
        flash(message, 'success')
    else:
        flash(message, 'danger')

    return redirect(url_for('host.booking_detail', booking_id=booking_id))


@host_bp.route('/bookings/<int:booking_id>/extension/reject', methods=['POST'])
@login_required
def reject_extension(booking_id):
    """
    Reject a user's extension request for a booking.
    This is the 'host.reject_extension' endpoint.
    """
    host = Host.query.filter_by(user_id=current_user.id).first_or_404()
    booking = Booking.query.get_or_404(booking_id)

    # Check if host owns the car for this booking
    if booking.car.host_id != host.id:
        flash('Access denied.')
        return redirect(url_for('host.dashboard'))

    # Check if extension can be rejected
    if not booking.can_reject_extension(host):
        flash('This extension request cannot be rejected.', 'warning')
        return redirect(url_for('host.booking_detail', booking_id=booking_id))

    # Attempt to reject
    success, message = booking.reject_extension(host)
    if success:
        db.session.commit()
        flash(message, 'info')
    else:
        flash(message, 'danger')

    return redirect(url_for('host.booking_detail', booking_id=booking_id))

# ... (rest of routes/host/bookings.py) ...


