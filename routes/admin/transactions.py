# routes/admin/transactions.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from . import admin_bp
from models import db
from models.booking import Booking
from models.car import Car
from models.user import User
from models.host import Host


@admin_bp.route('/transactions')
@login_required
def list_transactions():
    """
    List all transactions (payments, refunds, etc.) with search and pagination.
    This is the 'admin.list_transactions' endpoint.
    """
    # Authorization check
    if not hasattr(current_user, 'is_super_admin'):
        flash('Access denied.')
        return redirect(url_for('car.home'))

    page = request.args.get('page', 1, type=int)
    per_page = 20

    # Base query for transactions - Filter for completed/paid bookings
    # For now, we'll use Booking records as the source of transaction data
    # In a full implementation, you'd query a dedicated Transaction/WalletTransaction model
    query = Booking.query.join(Booking.car).join(Booking.user).join(Car.host).join(Car.host.user)
    query = query.filter(Booking.payment_status.in_(['completed', 'refunded', 'failed']))

    # Add search functionality
    search_query = request.args.get('search', '').strip()
    if search_query:
        query = query.filter(
            db.or_(
                db.cast(Booking.id, db.String).ilike(f"%{search_query}%"),
                Booking.razorpay_payment_id.ilike(f"%{search_query}%"),
                User.username.ilike(f"%{search_query}%"),
                User.email.ilike(f"%{search_query}%"),
                Car.make.ilike(f"%{search_query}%"),
                Car.model.ilike(f"%{search_query}%"),
                Car.host.user.username.ilike(f"%{search_query}%"),
                Car.host.company_name.ilike(f"%{search_query}%")
                # Add more searchable fields as needed
            )
        )

    # Add sorting
    sort_by = request.args.get('sort', 'date_desc')  # Default sort
    if sort_by == 'date_asc':
        query = query.order_by(Booking.payment_date.asc())
    elif sort_by == 'date_desc':
        query = query.order_by(Booking.payment_date.desc())
    elif sort_by == 'amount_asc':
        query = query.order_by(Booking.total_price.asc())
    elif sort_by == 'amount_desc':
        query = query.order_by(Booking.total_price.desc())
    else:
        query = query.order_by(Booking.payment_date.desc())  # Default

    transactions_pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    transactions = transactions_pagination.items

    return render_template('admin/transactions/list.html',
                           transactions=transactions,
                           transactions_pagination=transactions_pagination,
                           search_query=search_query,
                           current_sort=sort_by)

# ... (Add more transaction-related routes as needed, like viewing transaction details) ...