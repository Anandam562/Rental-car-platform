# models/wallet_transaction.py
from . import db
from datetime import datetime

class WalletTransaction(db.Model):
    __tablename__ = 'wallet_transactions'

    id = db.Column(db.Integer, primary_key=True)
    # --- CRITICAL FIX: Use String for Foreign Key ---
    # Use string 'users.id' instead of User.id to avoid circular import at module level
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    # --- END CRITICAL FIX ---

    # --- Transaction Details ---
    transaction_type = db.Column(db.String(20), nullable=False) # deposit, withdrawal, earning, deduction, refund, bonus, penalty
    amount = db.Column(db.Float, nullable=False) # The amount of the transaction
    balance_after = db.Column(db.Float, nullable=False) # Running balance after transaction
    description = db.Column(db.String(255), nullable=False) # Human-readable description
    # --- End Transaction Details ---

    # --- Reference to Related Entity ---
    # Allows linking this transaction to, e.g., a Booking, Host Earning, Admin Action
    reference_id = db.Column(db.Integer) # Generic ID
    reference_type = db.Column(db.String(50)) # 'booking', 'host_earning', 'admin_action', 'cancellation_fee', 'refund', etc.
    # --- End Reference ---

    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # --- CRITICAL FIX: Defer Relationship Definition ---
    # DO NOT define the 'user' relationship here using 'User' directly
    # The backref on User.wallet_transactions creates the 'user' attribute on WalletTransaction instances.
    # If you need to define it explicitly (not recommended with backref), use a string:
    # user = db.relationship('User', backref='wallet_transactions')
    # --- END CRITICAL FIX ---

    def __repr__(self):
        return f'<WalletTransaction {self.id}: {self.transaction_type} ₹{self.amount} for User {self.user_id}>'

    # --- CRITICAL FIX: Import User inside classmethod to avoid circular import ---
    @classmethod
    def record_transaction(cls, user, amount, transaction_type, description, reference_id=None, reference_type=None):
        """
        Record a wallet transaction for a user.
        Args:
            user (User): The User object.
            amount (float): The amount of the transaction.
            transaction_type (str): Type of transaction.
            description (str): Description of the transaction.
            reference_id (int, optional): ID of related entity.
            reference_type (str, optional): Type of related entity.
        Returns:
            WalletTransaction: The created transaction object.
        """
        # --- Import User inside the method to avoid circular import at module level ---
        from .user import User # Import User model INSIDE the method
        # --- END Import ---

        # --- Validate Inputs ---
        if not isinstance(user, User):
            raise ValueError("Invalid user object provided to record_transaction.")
        if not isinstance(amount, (int, float)) or amount <= 0:
            raise ValueError("Invalid amount provided to record_transaction.")
        if not isinstance(transaction_type, str) or not transaction_type.strip():
            raise ValueError("Invalid transaction_type provided to record_transaction.")
        if not isinstance(description, str) or not description.strip():
            raise ValueError("Invalid description provided to record_transaction.")
        # --- End Validation ---

        # Calculate new balance based on transaction type
        if transaction_type in ['deposit', 'earning', 'refund', 'bonus']:
            new_balance = user.wallet_balance + amount
        elif transaction_type in ['withdrawal', 'deduction', 'penalty']:
            new_balance = user.wallet_balance - amount
        else:
            raise ValueError(f"Invalid transaction type: {transaction_type}")

        # Create transaction record
        transaction = cls(
            user_id=user.id,
            amount=round(amount, 2),
            transaction_type=transaction_type,
            description=description[:255], # Truncate description
            balance_after=round(new_balance, 2),
            reference_id=reference_id,
            reference_type=reference_type,
            timestamp=datetime.utcnow()
        )

        # Update user's wallet balance in memory (actual DB update happens in calling function)
        # This assumes user.add_to_wallet/deduct_from_wallet handles DB persistence
        if transaction_type in ['deposit', 'earning', 'refund', 'bonus']:
            user.wallet_balance = new_balance # Update in memory
        elif transaction_type in ['withdrawal', 'deduction', 'penalty']:
            user.wallet_balance = new_balance # Update in memory

        db.session.add(transaction) # Add transaction to session
        # Note: Don't commit here, let the caller handle the transaction
        return transaction
    # --- END CRITICAL FIX ---

# --- Helper Methods for Recording Specific Transaction Types ---
# These can be called from booking/host logic to record specific events

    @classmethod
    def record_booking_payment(cls, user, booking, amount_paid):
        """Record a user paying for a booking."""
        description = f"Payment for Booking #{booking.id}"
        return cls.record_transaction(
            user=user,
            amount=amount_paid,
            transaction_type='deduction', # User pays out
            description=description,
            reference_id=booking.id,
            reference_type='booking_payment'
        )

    @classmethod
    def record_booking_refund(cls, user, booking, refund_amount):
        """Record a refund issued to a user for a booking."""
        description = f"Refund for Booking #{booking.id}"
        return cls.record_transaction(
            user=user,
            amount=refund_amount,
            transaction_type='refund', # User receives money back
            description=description,
            reference_id=booking.id,
            reference_type='booking_refund'
        )

    @classmethod
    def record_host_earning(cls, host_user, booking, earning_amount): # Pass the User object associated with the host
        """Record earnings credited to a host's wallet for a completed booking."""
        description = f"Earnings from Booking #{booking.id}"
        return cls.record_transaction(
            user=host_user, # The User object linked to the Host
            amount=earning_amount,
            transaction_type='earning', # Host earns money
            description=description,
            reference_id=booking.id,
            reference_type='host_earning'
        )

    @classmethod
    def record_cancellation_fee(cls, user, booking, fee_amount):
        """Record a cancellation fee deducted from a user's wallet."""
        description = f"Cancellation Fee for Booking #{booking.id}"
        return cls.record_transaction(
            user=user,
            amount=fee_amount,
            transaction_type='deduction', # User pays fee
            description=description,
            reference_id=booking.id,
            reference_type='cancellation_fee'
        )

    @classmethod
    def record_manual_adjustment(cls, user, amount, admin_user, reason):
        """Record a manual adjustment made by an admin."""
        transaction_type = 'deposit' if amount >= 0 else 'deduction'
        description = f"Manual Adjustment by {admin_user.username}: {reason}"
        # Use absolute value for amount if deduction logic is handled by transaction_type
        abs_amount = abs(amount)
        return cls.record_transaction(
            user=user,
            amount=abs_amount,
            transaction_type=transaction_type,
            description=description,
            reference_id=admin_user.id, # Reference admin who made the adjustment
            reference_type='admin_adjustment'
        )

    @classmethod
    def record_deposit(cls, user, amount, payment_method_details=""):
        """Record a user depositing money into their wallet."""
        description = f"Deposit via {payment_method_details}" if payment_method_details else "Wallet Deposit"
        return cls.record_transaction(
            user=user,
            amount=amount,
            transaction_type='deposit',
            description=description,
            reference_type='deposit' # No specific reference ID needed unless tied to a payment gateway transaction
        )

    @classmethod
    def record_withdrawal(cls, user, amount, withdrawal_reference=""):
        """Record a user withdrawing money from their wallet."""
        description = f"Withdrawal Request {withdrawal_reference}" if withdrawal_reference else "Wallet Withdrawal"
        return cls.record_transaction(
            user=user,
            amount=amount,
            transaction_type='withdrawal',
            description=description,
            reference_id=user.id, # Or a specific withdrawal request ID
            reference_type='withdrawal'
        )
# --- End Helper Methods ---
# --- End WalletTransaction Model ---