# models/host.py
from . import db
from datetime import datetime

# models/host.py
from . import db
from datetime import datetime

from .host_bank_account import HostBankAccount


class Host(db.Model):
    __tablename__ = 'hosts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    company_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)

    # --- ADD THESE LOCATION COLUMNS ---
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    full_address = db.Column(db.String(500))
    street_address = db.Column(db.String(255))
    locality = db.Column(db.String(100))
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    pincode = db.Column(db.String(20))
    # --- END ADD ---

    is_verified = db.Column(db.Boolean, default=False)
    wallet_balance = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


    # --- Relationship Definitions ---
    # DO NOT DEFINE 'user' relationship here if using backref.
    # The 'backref' on User.host_profile creates a 'user' attribute on Host instances.
    # Example expected setup in User model:
    # host_profile = db.relationship('Host', backref='user')
    #
    # If you were using back_populates instead, you would define them here like:
    # user = db.relationship('User', back_populates='host_profile')
    # AND in User model: back_populates='host_profile'
    # --- END RELATIONSHIPS ---

    def __repr__(self):
        user_info = f" (User ID: {self.user_id})" if self.user_id else ""
        name = self.company_name or (self.user.username if self.user else "No Name")
        return f'<Host {name}{user_info}>'

        # --- CRITICAL FIX: Update Wallet Interaction Methods ---
        # Remove db.session.commit() from add_to_wallet and deduct_from_wallet
        # Let the calling function handle the commit to ensure atomicity
    def add_to_wallet(self, amount):
        """
        Add funds to the host's wallet.
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
        Deduct funds from the host's wallet.
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
    # --- END CRITICAL FIX ---
    # --- End Wallet Interaction Methods ---

# # --- Host Rating Model ---
# class HostRating(db.Model):
#     __tablename__ = 'host_ratings'
#
#     id = db.Column(db.Integer, primary_key=True)
#     host_id = db.Column(db.Integer, db.ForeignKey('hosts.id'), nullable=False)
#     user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
#     rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
#     comment = db.Column(db.Text)
#     created_at = db.Column(db.DateTime, default=datetime.utcnow)
#
#     # --- Relationship Definitions ---
#     # DO NOT DEFINE 'host' or 'user' relationships here.
#     # They are provided automatically by the 'backref' defined in Host and User models.
#     # - Host.ratings backref='host' creates a 'host' attribute on HostRating.
#     # - User.host_ratings_given backref='user' creates a 'user' attribute on HostRating.
#     # --- End Relationships ---
#
#     def __repr__(self):
#         return f'<HostRating {self.rating} stars for Host {self.host_id}>'
#
# # --- Host Feedback Model ---
# class HostFeedback(db.Model):
#     __tablename__ = 'host_feedbacks'
#
#     id = db.Column(db.Integer, primary_key=True)
#     host_id = db.Column(db.Integer, db.ForeignKey('hosts.id'), nullable=False)
#     user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
#     subject = db.Column(db.String(100))
#     message = db.Column(db.Text, nullable=False)
#     is_resolved = db.Column(db.Boolean, default=False)
#     created_at = db.Column(db.DateTime, default=datetime.utcnow)
#
#     # --- Relationship Definitions ---
#     # DO NOT DEFINE 'host' or 'user' relationships here.
#     # They are provided automatically by the 'backref' defined in Host and User models.
#     # - Host.feedbacks backref='host' creates a 'host' attribute on HostFeedback.
#     # - User.feedbacks_given backref='user' creates a 'user' attribute on HostFeedback.
#     # --- End Relationships ---
#
#     def __repr__(self):
#         status = "Resolved" if self.is_resolved else "Pending"
#         return f'<HostFeedback {self.subject} ({status}) for Host {self.host_id}>'

# --- NEW: Bank Account Methods ---
    def get_primary_bank_account(self):
        """Get the host's primary bank account."""
        return HostBankAccount.query.filter_by(host_id=self.id, is_primary=True).first()

    def get_all_bank_accounts(self):
        """Get all bank accounts linked to the host."""
        return HostBankAccount.query.filter_by(host_id=self.id).all()

    def add_bank_account(self, bank_name, account_holder_name, account_number, ifsc_code, branch_name=""):
        """Add a new bank account for the host."""
        # Check if this is the first account, make it primary
        existing_accounts = self.get_all_bank_accounts()
        is_primary = len(existing_accounts) == 0

        new_account = HostBankAccount(
            host_id=self.id,
            bank_name=bank_name,
            account_holder_name=account_holder_name,
            account_number=account_number, # Encrypt in production
            ifsc_code=ifsc_code,
            branch_name=branch_name,
            is_primary=is_primary,
            is_verified=False # Needs verification
        )
        db.session.add(new_account)
        # Don't commit here, let the calling function handle it
        return new_account

    def remove_bank_account(self, account_id):
        """Remove a bank account linked to the host."""
        account = HostBankAccount.query.get(account_id)
        if account and account.host_id == self.id:
            # If removing primary account, set another one as primary if available
            if account.is_primary:
                other_accounts = HostBankAccount.query.filter(
                    HostBankAccount.host_id == self.id,
                    HostBankAccount.id != account_id
                ).all()
                if other_accounts:
                    other_accounts[0].set_as_primary() # Set first available as primary
            db.session.delete(account)
            # Don't commit here, let the calling function handle it
            return True
        return False

    def set_primary_bank_account(self, account_id):
        """Set a specific bank account as the primary account."""
        account = HostBankAccount.query.get(account_id)
        if account and account.host_id == self.id:
            account.set_as_primary() # Use the method in HostBankAccount model
            # Don't commit here, let the calling function handle it
            return True
        return False
    # --- END NEW: Bank Account Methods ---
    # --- End Wallet Interaction Methods ---