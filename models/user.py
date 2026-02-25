# models/user.py (Relevant part)
from . import db
from datetime import datetime
import bcrypt
from flask_login import UserMixin

from .wallet_transaction import WalletTransaction


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    phone = db.Column(db.String(20))
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)  # For Flask-Login
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Add wallet balance field
    wallet_balance = db.Column(db.Float, default=0.0)  # Add this if missing

    # --- CRITICAL: Ensure this relationship is defined correctly ---
    # This line creates a 'bookings' attribute on User instances
    # AND automatically creates a 'user' attribute on Booking instances via backref.
    bookings = db.relationship('Booking', backref='user', lazy=True)  # <-- MAKE SURE THIS LINE EXISTS
    # --- END CRITICAL ---

    # --- Host Profile Relationship (if applicable) ---
    # This creates a 'host_profile' attribute on User instances
    # AND automatically creates a 'user' attribute on Host instances via backref.
    host_profile = db.relationship('Host', backref='user', uselist=False, lazy=True)  # One user, one host profile

    # --- End Host Profile ---

    def set_password(self, password):
        """Hash and set the user's password."""
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password):
        """Check if the provided password matches the stored hash."""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

    def add_to_wallet(self, amount):
        """
        Add funds to the user's wallet.
        Args:
            amount (float): The amount to add (positive value).
        Returns:
            bool: True if successful, False otherwise.
        """
        if amount > 0:
            self.wallet_balance += amount
            db.session.add(self)  # Add the modified object to the session
            # --- CRITICAL FIX: DO NOT COMMIT HERE ---
            # db.session.commit() # <-- REMOVE THIS LINE
            # --- END CRITICAL FIX ---
            return True
        return False

    def deduct_from_wallet(self, amount):
        """
        Deduct funds from the user's wallet.
        Args:
            amount (float): The amount to deduct (positive value).
        Returns:
            bool: True if successful (sufficient balance), False otherwise.
        """
        if amount > 0 and self.wallet_balance >= amount:
            self.wallet_balance -= amount
            db.session.add(self)  # Add the modified object to the session
            # --- CRITICAL FIX: DO NOT COMMIT HERE ---
            # db.session.commit() # <-- REMOVE THIS LINE
            # --- END CRITICAL FIX ---
            return True
        return False

    def __repr__(self):
        return f'<User {self.username}>'

    def get_wallet_transactions(self, limit=None):
        """
        Get the user's wallet transactions, sorted by timestamp descending.
        Args:
            limit (int, optional): Maximum number of transactions to return.
        Returns:
            list: List of WalletTransaction objects.
        """
        query = WalletTransaction.query.filter_by(user_id=self.id).order_by(
            WalletTransaction.timestamp.desc()
        )
        if limit:
            query = query.limit(limit)
        return query.all()