# routes/host/profile.py
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from . import host_bp
from models import db
from models.host import Host


# If you create a WalletTransaction model later, import it here
# from models.wallet import WalletTransaction

@host_bp.route('/profile/wallet')  # <-- This creates the 'host.wallet' endpoint
@login_required
def wallet1():#Rename if require to Dashboard
    """Display host's wallet information and transaction history"""
    host = Host.query.filter_by(user_id=current_user.id).first_or_404()

    # For now, just pass the host object which contains wallet_balance
    # In a full implementation, you'd query a Transaction/WalletHistory model

    # Example placeholder data (replace with real queries)
    # transactions = WalletTransaction.query.filter_by(host_id=host.id).order_by(WalletTransaction.created_at.desc()).limit(10).all()
    transactions = []  # Placeholder

    return render_template('host/profile/wallet.html', host=host, transactions=transactions)

# Optional: Route for withdrawal requests (requires more logic)
# @host_bp.route('/profile/wallet/withdraw', methods=['GET', 'POST'])
# @login_required
# def withdraw_funds():
#     host = Host.query.filter_by(user_id=current_user.id).first_or_404()
#     # Logic for withdrawal form and processing
#     # if request.method == 'POST':
#     #     amount = float(request.form.get('amount', 0))
#     #     bank_account_id = int(request.form.get('bank_account'))
#     #     # ... validation and processing ...
#     # return render_template('host/profile/withdraw.html', host=host)
#     pass
