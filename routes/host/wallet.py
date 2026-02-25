# routes/host/wallet.py (New File)
from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from . import host_bp
from models import db
# Import Host to access wallet methods
from models.host import Host
# Import WalletTransaction for wallet history
from models.wallet_transaction import WalletTransaction
# Import HostBankAccount for bank account management
from models.host_bank_account import HostBankAccount

@host_bp.route('/wallet')
@host_bp.route('/wallet/history') # Alias route for clarity
@login_required
def wallet():
    """
    Display the host's wallet balance and full transaction history.
    This is the 'host.wallet' endpoint.
    """
    # --- Fetch Host Profile ---
    # Get the host profile associated with the current user
    host = Host.query.filter_by(user_id=current_user.id).first_or_404()
    # --- End Fetch Host Profile ---

    # --- Fetch Wallet Data ---
    wallet_balance = host.wallet_balance # Get wallet balance from Host object

    # Fetch recent wallet transactions with pagination
    page = request.args.get('page', 1, type=int)
    per_page = 10 # Number of transactions per page

    transactions_query = WalletTransaction.query.filter_by(
        user_id=host.user_id # Filter by host's user ID (wallet transactions are linked to User)
    ).order_by(
        WalletTransaction.timestamp.desc() # Order by timestamp descending (newest first)
    )

    transactions_pagination = transactions_query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    transactions = transactions_pagination.items
    # --- End Fetch Wallet Data ---

    # --- Prepare Context for Template ---
    context = {
        'host': host, # Pass the host object
        'wallet_balance': wallet_balance, # Pass the wallet balance
        'transactions': transactions, # Pass the list of transactions
        'transactions_pagination': transactions_pagination # Pass the pagination object
    }
    # --- End Context ---

    # --- Render Template ---
    return render_template('host/wallet/list.html', **context)
    # --- End Render ---
# --- End Wallet Route ---

# --- NEW: Transaction Detail Route ---
@host_bp.route('/wallet/transactions/<int:transaction_id>')
@login_required
def wallet_transaction_detail(transaction_id):
    """
    Display detailed information for a specific wallet transaction.
    This is the 'host.wallet_transaction_detail' endpoint.
    """
    # --- Fetch Host Profile ---
    # Get the host profile associated with the current user
    host = Host.query.filter_by(user_id=current_user.id).first_or_404()
    # --- End Fetch Host Profile ---

    # Fetch the transaction
    transaction = WalletTransaction.query.get_or_404(transaction_id)

    # Authorization: Ensure the transaction belongs to the current host (via user_id)
    if transaction.user_id != host.user_id:
        flash('Access denied.')
        return redirect(url_for('car.home')) # Or redirect to a more appropriate page

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
        'host': host, # Pass the host object
        'transaction': transaction, # Pass the transaction object
        'related_object': related_object # Pass the related object to the template
    }
    # --- End Context ---

    # --- Render Template ---
    return render_template('host/wallet/detail.html', **context)
    # --- End Render ---
# --- END NEW: Transaction Detail Route ---

# --- NEW: Bank Accounts Management Routes ---
@host_bp.route('/wallet/bank_accounts')
@login_required
def list_bank_accounts():
    """
    List all bank accounts linked to the host.
    This is the 'host.list_bank_accounts' endpoint.
    """
    host = Host.query.filter_by(user_id=current_user.id).first_or_404()
    bank_accounts = host.get_all_bank_accounts()
    return render_template('host/wallet/bank_accounts/list.html', host=host, bank_accounts=bank_accounts)

@host_bp.route('/wallet/bank_accounts/add', methods=['GET', 'POST'])
@login_required
def add_bank_account():
    """
    Add a new bank account for the host.
    This is the 'host.add_bank_account' endpoint.
    """
    host = Host.query.filter_by(user_id=current_user.id).first_or_404()

    if request.method == 'POST':
        bank_name = request.form.get('bank_name', '').strip()
        account_holder_name = request.form.get('account_holder_name', '').strip()
        account_number = request.form.get('account_number', '').strip()
        ifsc_code = request.form.get('ifsc_code', '').strip().upper() # IFSC codes are uppercase
        branch_name = request.form.get('branch_name', '').strip()

        # Basic validation (add more as needed)
        if not all([bank_name, account_holder_name, account_number, ifsc_code]):
            flash('All fields except Branch Name are required.', 'danger')
            return render_template('host/wallet/bank_accounts/add.html', host=host)

        # Check for duplicate account number (simple check)
        existing_account = HostBankAccount.query.filter_by(
            host_id=host.id,
            account_number=account_number
        ).first()
        if existing_account:
            flash('This account number is already linked to your profile.', 'danger')
            return render_template('host/wallet/bank_accounts/add.html', host=host)

        try:
            new_account = host.add_bank_account(
                bank_name=bank_name,
                account_holder_name=account_holder_name,
                account_number=account_number,
                ifsc_code=ifsc_code,
                branch_name=branch_name
            )
            db.session.commit()
            flash('Bank account added successfully! It needs to be verified.', 'success')
            return redirect(url_for('host.list_bank_accounts'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error adding bank account for host {host.id}: {e}")
            flash('An error occurred while adding the bank account. Please try again.', 'danger')
            return render_template('host/wallet/bank_accounts/add.html', host=host)

    return render_template('host/wallet/bank_accounts/add.html', host=host)

@host_bp.route('/wallet/bank_accounts/<int:account_id>/remove', methods=['POST'])
@login_required
def remove_bank_account(account_id):
    """
    Remove a bank account linked to the host.
    This is the 'host.remove_bank_account' endpoint.
    """
    host = Host.query.filter_by(user_id=current_user.id).first_or_404()

    try:
        if host.remove_bank_account(account_id):
            db.session.commit()
            flash('Bank account removed successfully.', 'success')
        else:
            flash('Failed to remove bank account. Please try again.', 'danger')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error removing bank account {account_id} for host {host.id}: {e}")
        flash('An error occurred while removing the bank account. Please try again.', 'danger')

    return redirect(url_for('host.list_bank_accounts'))

@host_bp.route('/wallet/bank_accounts/<int:account_id>/set_primary', methods=['POST'])
@login_required
def set_primary_bank_account(account_id):
    """
    Set a specific bank account as the primary account for the host.
    This is the 'host.set_primary_bank_account' endpoint.
    """
    host = Host.query.filter_by(user_id=current_user.id).first_or_404()

    try:
        if host.set_primary_bank_account(account_id):
            db.session.commit()
            flash('Primary bank account updated successfully.', 'success')
        else:
            flash('Failed to update primary bank account. Please try again.', 'danger')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error setting primary bank account {account_id} for host {host.id}: {e}")
        flash('An error occurred while updating the primary bank account. Please try again.', 'danger')

    return redirect(url_for('host.list_bank_accounts'))
# --- END NEW: Bank Accounts Management Routes ---

# routes/host/wallet.py (Inside the withdraw_funds function)
# ... (previous imports and route definition) ...

@host_bp.route('/wallet/withdraw', methods=['GET', 'POST'])
@login_required
def withdraw_funds():
    """
    Placeholder for withdrawing funds from the host's wallet.
    This is the 'host.withdraw_funds' endpoint.
    Implement logic for withdrawal requests and processing.
    """
    host = Host.query.filter_by(user_id=current_user.id).first_or_404()

    if request.method == 'POST':
        amount_str = request.form.get('amount')
        account_id_str = request.form.get('account_id') # Get selected account ID

        try:
            amount = float(amount_str)
            account_id = int(account_id_str)
        except (ValueError, TypeError):
            flash('Invalid amount or account selected.', 'danger')
            return render_template('host/wallet/withdraw.html', host=host, bank_accounts=host.get_all_bank_accounts())

        if amount <= 0:
            flash('Amount must be greater than zero.', 'danger')
            return render_template('host/wallet/withdraw.html', host=host, bank_accounts=host.get_all_bank_accounts())

        # --- Check Wallet Balance ---
        if host.wallet_balance < amount:
            flash('Insufficient funds in your wallet.', 'danger')
            return render_template('host/wallet/withdraw.html', host=host, bank_accounts=host.get_all_bank_accounts())
        # --- END Check Wallet Balance ---

        # --- Validate Selected Account ---
        selected_account = HostBankAccount.query.get(account_id)
        if not selected_account or selected_account.host_id != host.id:
            flash('Invalid bank account selected.', 'danger')
            return render_template('host/wallet/withdraw.html', host=host, bank_accounts=host.get_all_bank_accounts())
        # --- END Validate Selected Account ---

        # --- CRITICAL FIX: Implement Withdrawal Request Logic ---
        # This creates a withdrawal request record in the database.
        # It deducts the amount from the host's wallet balance (in memory).
        # It records the transaction as 'withdrawal' (using the existing method).
        # It notifies the admin (placeholder).
        # It redirects to the wallet page with a success message.
        try:
            # --- CRITICAL FIX: Use existing record_withdrawal method ---
            # Record the withdrawal transaction using the existing helper method
            # This deducts the amount from host.wallet_balance in memory and records the transaction
            WalletTransaction.record_withdrawal( # <-- Use record_withdrawal, NOT record_withdrawal_request
                user=host.user, # Pass the User object associated with the host
                amount=amount,
                withdrawal_reference=f"Requested to {selected_account.bank_name} ({selected_account.mask_account_number()})" # Add account details to reference
            )
            # --- END CRITICAL FIX ---
            db.session.commit() # Commit the transaction record and wallet balance update

            # --- CRITICAL FIX: Send Notification to Host ---
            # Send notification to host after successful withdrawal request
            from utils.notification_sender import send_notification_to_host
            send_notification_to_host(
                host_user_id=host.user_id, # Pass the host's user ID
                message=f"Withdrawal request of ₹{amount:.2f} initiated to {selected_account.bank_name} ({selected_account.mask_account_number()}). Awaiting admin approval."
            )
            # --- END CRITICAL FIX ---

            # --- CRITICAL FIX: Send Notification to Admin (Placeholder) ---
            # Notify Admin (placeholder - implement notification logic)
            # You might want to create a separate AdminNotification model or use a general notification system
            print(f"[ADMIN NOTIFICATION] Host {host.user.username} requested withdrawal of ₹{amount:.2f} to {selected_account.bank_name} ({selected_account.mask_account_number()}).") # Log for now
            # --- END CRITICAL FIX ---

            flash(f'Withdrawal request of ₹{amount:.2f} initiated successfully! Awaiting admin approval.', 'success')
            return redirect(url_for('host.wallet')) # Redirect to wallet page

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error processing withdrawal request for host {host.id}: {e}")
            flash('An error occurred while processing your withdrawal request. Please try again.', 'danger')
            return render_template('host/wallet/withdraw.html', host=host, bank_accounts=host.get_all_bank_accounts())
        # --- END CRITICAL FIX ---

    # GET request: Show the withdrawal form
    return render_template('host/wallet/withdraw.html', host=host, bank_accounts=host.get_all_bank_accounts())
# --- END NEW: Withdraw Funds Route ---
# --- End Wallet Routes ---