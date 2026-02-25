# models/admin.py
from . import db
from datetime import datetime
import bcrypt
from flask_login import UserMixin

class Admin(UserMixin, db.Model):
    __tablename__ = 'admins'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    # --- CRITICAL FIX 1: Add Access Level ---
    # Define access levels (e.g., 'super', 'support', 'finance', 'content')
    access_level = db.Column(db.String(20), default='support') # Default level
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # --- END CRITICAL FIX 1 ---

    def set_password(self, password):
        """Hash and set the admin's password."""
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password):
        """Check if the provided password matches the stored hash."""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

    def __repr__(self):
        return f'<Admin {self.username} ({self.access_level})>'

    # --- CRITICAL FIX 2: Check Access Level ---
    def has_access(self, required_level):
        """
        Check if admin has the required access level.
        Super admins have access to everything.
        Other levels might have specific permissions.
        """
        if self.access_level == 'super':
            return True
        # Define access hierarchy or specific permissions per level
        # Example simple hierarchy: super > support > finance > content
        level_hierarchy = {
            'super': 4,
            'support': 3,
            'finance': 2,
            'content': 1
        }
        required_rank = level_hierarchy.get(required_level, 0)
        admin_rank = level_hierarchy.get(self.access_level, 0)
        return admin_rank >= required_rank

    def can_manage_admins(self):
        """Check if admin can manage other admins (typically super admins)."""
        return self.has_access('super')
    # --- END CRITICAL FIX 2 ---

# --- Helper Function to Create Default Admin ---
def create_default_admin():
    """Create a default admin user if one doesn't exist."""
    # Check if any admin exists
    existing_admin = Admin.query.first()
    if not existing_admin:
        # Create default admin
        default_admin = Admin(
            username='admin',
            email='admin@zoomcarclone.com',
            access_level='super' # Make default admin a super admin
        )
        default_admin.set_password('123') # Default password
        db.session.add(default_admin)
        try:
            db.session.commit()
            print("Default SUPER admin user 'admin' created with password '123'. Please change this immediately!")
        except Exception as e:
            db.session.rollback()
            print(f"Error creating default admin: {e}")
    else:
        print("Admin user already exists. Skipping default admin creation.")
# --- End Helper Function ---
