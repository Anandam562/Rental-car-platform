# models/host_bank_account.py (New File)
from . import db
from datetime import datetime

class HostBankAccount(db.Model):
    __tablename__ = 'host_bank_accounts'

    id = db.Column(db.Integer, primary_key=True)
    host_id = db.Column(db.Integer, db.ForeignKey('hosts.id'), nullable=False) # Link to Host
    bank_name = db.Column(db.String(100), nullable=False)
    account_holder_name = db.Column(db.String(100), nullable=False)
    account_number = db.Column(db.String(50), nullable=False) # Encrypted in production
    ifsc_code = db.Column(db.String(20), nullable=False) # Indian Financial System Code
    branch_name = db.Column(db.String(100))
    is_primary = db.Column(db.Boolean, default=False) # Flag for primary account
    is_verified = db.Column(db.Boolean, default=False) # Verification status
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # --- Relationship Definitions ---
    host = db.relationship('Host', backref='bank_accounts') # Backref to Host
    # --- End Relationships ---

    def __repr__(self):
        masked_acc_no = "*" * (len(self.account_number) - 4) + self.account_number[-4:] if self.account_number else "N/A"
        return f'<HostBankAccount {self.bank_name} ({masked_acc_no}) for Host {self.host_id}>'

    def mask_account_number(self):
        """Mask the account number for display."""
        if self.account_number:
            return "*" * (len(self.account_number) - 4) + self.account_number[-4:]
        return "N/A"

    def set_as_primary(self):
        """Set this account as the primary account for the host."""
        # Ensure only one primary account per host
        HostBankAccount.query.filter_by(host_id=self.host_id, is_primary=True).update({HostBankAccount.is_primary: False})
        self.is_primary = True
        db.session.add(self)
        # Don't commit here, let the caller handle it

    def verify_account(self):
        """Mark the account as verified (placeholder for actual verification logic)."""
        self.is_verified = True
        db.session.add(self)
        # Don't commit here, let the caller handle it
# --- End HostBankAccount Model ---