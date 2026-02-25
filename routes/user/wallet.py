# routes/user/wallet.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from . import user_bp
from models import db
# Import WalletTransaction
from models.wallet_transaction import WalletTransaction

@user_bp.route('/wallet')
@user_bp.route('/wallet/history') # Alias route for clarity
@login_required
def wallet():
    """
    Display the user's wallet balance and full transaction history.
    This is the 'user.wallet' endpoint.
    """
    # --- Fetch Wallet Data ---
    wallet_balance = current_user.wallet_balance
    # --- End Fetch Wallet Data ---

    # --- Fetch All Transactions with Pagination ---
    page = request.args.get('page', 1, type=int)
    per_page = 10 # Number of transactions per page

    transactions_query = WalletTransaction.query.filter_by(
        user_id=current_user.id
    ).order_by(
        WalletTransaction.timestamp.desc()
    )

    transactions_pagination = transactions_query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    transactions = transactions_pagination.items
    # --- End Fetch Transactions ---

    # --- Prepare Context for Template ---
    context = {
        'wallet_balance': wallet_balance,
        'transactions': transactions,
        'transactions_pagination': transactions_pagination
    }
    # --- End Context ---

    # --- Render Template ---
    return render_template('user/wallet/list.html', **context)
    # --- End Render ---

# --- NEW: Transaction Detail Route ---
@user_bp.route('/wallet/transactions/<int:transaction_id>')
@login_required
def wallet_transaction_detail(transaction_id):
    """
    Display detailed information for a specific wallet transaction.
    This is the 'user.wallet_transaction_detail' endpoint.
    """
    # Fetch the transaction
    transaction = WalletTransaction.query.get_or_404(transaction_id)

    # Authorization: Ensure the transaction belongs to the current user
    if transaction.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('user.wallet'))

    # --- Prepare Context for Template ---
    # You might want to fetch related objects based on reference_type/reference_id
    # For example, if reference_type is 'booking', fetch the Booking object
    related_object = None
    if transaction.reference_type == 'booking' and transaction.reference_id:
        from models.booking import Booking
        related_object = Booking.query.get(transaction.reference_id)
    elif transaction.reference_type == 'host_earning' and transaction.reference_id:
         # Example: if reference_id points to a Booking, fetch it
         from models.booking import Booking
         related_object = Booking.query.get(transaction.reference_id)
    # Add more elif blocks for other reference_types as needed

    context = {
        'transaction': transaction,
        'related_object': related_object # Pass the related object to the template
    }
    # --- End Context ---

    # --- Render Template ---
    return render_template('user/wallet/detail.html', **context)
    # --- End Render ---
# --- END NEW: Transaction Detail Route ---

