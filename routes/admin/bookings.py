# routes/admin/bookings.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from . import admin_bp
from models import db
from models.booking import Booking
from models.car import Car
from models.user import User
from models.host import Host


@admin_bp.route('/bookings')
@login_required
def list_bookings():
    """
    List all bookings with search and pagination.
    This is the 'admin.list_bookings' endpoint.
    """
    # Authorization check
    if not hasattr(current_user, 'is_super_admin'):
        flash('Access denied.')
        return redirect(url_for('car.home'))

    page = request.args.get('page', 1, type=int)
    per_page = 20

    # Base query - Join for comprehensive data
    query = Booking.query.join(Booking.car).join(Booking.user).join(Car.host).join(Car.host.user)

    # Search functionality
    search_query = request.args.get('search', '').strip()
    if search_query:
        query = query.filter(
            db.or_(
                db.cast(Booking.id, db.String).ilike(f"%{search_query}%"),
                Car.make.ilike(f"%{search_query}%"),
                Car.model.ilike(f"%{search_query}%"),
                User.username.ilike(f"%{search_query}%"),
                User.email.ilike(f"%{search_query}%"),
                Car.host.user.username.ilike(f"%{search_query}%"),
                Car.host.company_name.ilike(f"%{search_query}%")
                # Add more searchable fields as needed (dates, status)
            )
        )

    # Paginate results
    bookings_pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    bookings = bookings_pagination.items

    return render_template('admin/bookings/list.html',
                           bookings=bookings,
                           bookings_pagination=bookings_pagination,
                           search_query=search_query)


@admin_bp.route('/bookings/<int:booking_id>')
@login_required
def booking_detail(booking_id):
    """
    View detailed information for a specific booking.
    This is the 'admin.booking_detail' endpoint.
    """
    # Authorization check
    if not hasattr(current_user, 'is_super_admin'):
        flash('Access denied.')
        return redirect(url_for('car.home'))

    booking = Booking.query.get_or_404(booking_id)
    # The relationships should load car, user, and host details

    return render_template('admin/bookings/detail.html', booking=booking)


@admin_bp.route('/bookings/<int:booking_id>/cancel', methods=['POST'])
@login_required
def cancel_booking(booking_id):
    """
    Cancel a booking by admin.
    This is the 'admin.cancel_booking' endpoint.
    """
    # Authorization check
    if not hasattr(current_user, 'is_super_admin'):
        flash('Access denied.')
        return redirect(url_for('car.home'))

    booking = Booking.query.get_or_404(booking_id)

    reason = request.form.get('reason', '').strip()
    if not reason:
        flash('Please provide a reason for cancellation.', 'danger')
        return redirect(url_for('admin.booking_detail', booking_id=booking_id))

    # Attempt to cancel
    if booking.cancel_by_admin(reason=reason):
        db.session.commit()
        flash(f'Booking #{booking.id} cancelled successfully by admin.', 'success')
    else:
        flash('Failed to cancel booking.', 'danger')

    return redirect(url_for('admin.booking_detail', booking_id=booking_id))