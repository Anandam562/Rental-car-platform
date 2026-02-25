# routes/host/payment.py
from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from . import host_bp
from models import db
from models.host import Host
from models.booking import Booking


# If you create a dedicated Payment model later, import it here
# from models.payment import Payment

@host_bp.route('/payments')
@login_required
def list_payments():
    """Display host's payment history"""
    host = Host.query.filter_by(user_id=current_user.id).first_or_404()

    # Query bookings related to this host's cars
    # For a more complex system, you'd have a dedicated Payment/Transaction model
    # linked to bookings or host wallet changes.
    # This example assumes earnings are tied directly to bookings.

    # Get all bookings for cars owned by this host
    bookings_query = Booking.query.join(Booking.car).filter(
        Booking.car.has(host_id=host.id)
    ).order_by(Booking.created_at.desc())

    # Simple pagination (optional, but good practice)
    page = request.args.get('page', 1, type=int)
    per_page = 10
    bookings_pagination = bookings_query.paginate(page=page, per_page=per_page, error_out=False)
    bookings = bookings_pagination.items

    # Calculate summary statistics
    total_earnings = sum(b.total_price for b in bookings if b.status == 'completed')  # Simplified
    pending_earnings = sum(b.total_price for b in bookings if b.status in ['pending', 'confirmed'])

    return render_template(
        'host/payments/list.html',
        host=host,
        bookings=bookings,
        bookings_pagination=bookings_pagination,
        total_earnings=total_earnings,
        pending_earnings=pending_earnings
    )

# Optional: Route for payment details (if you add a Payment model)
# @host_bp.route('/payments/<int:payment_id>')
# @login_required
# def payment_detail(payment_id):
#     host = Host.query.filter_by(user_id=current_user.id).first_or_404()
#     # Logic to fetch specific payment details
#     # payment = Payment.query.get_or_404(payment_id)
#     # ... check ownership ...
#     # return render_template('host/payments/detail.html', payment=payment)
#     pass

# Optional: Route for withdrawal requests (requires more logic and models)
# @host_bp.route('/payments/withdraw', methods=['GET', 'POST'])
# @login_required
# def withdraw_funds():
#     host = Host.query.filter_by(user_id=current_user.id).first_or_404()
#     # Logic for withdrawal form and processing
#     # if request.method == 'POST':
#     #     amount = float(request.form.get('amount', 0))
#     #     bank_account_id = int(request.form.get('bank_account'))
#     #     # ... validation and processing ...
#     # return render_template('host/payments/withdraw.html', host=host)
#     pass