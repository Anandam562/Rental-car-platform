# models/notification.py
"""
Notification model for storing user/host notifications in the database.
This defines the structure of the 'notifications' table.
"""

# Import necessary modules from SQLAlchemy and datetime
from . import db  # Import the db instance from the models package __init__.py
from datetime import datetime  # Import datetime for timestamp

class Notification(db.Model):
    """
    Represents a notification sent to a user or host.
    This model defines the 'notifications' table schema.
    """
    # --- Table Definition ---
    __tablename__ = 'notifications'  # Name of the database table
    # --- End Table Definition ---

    # --- Column Definitions ---
    # Unique identifier for the notification
    id = db.Column(db.Integer, primary_key=True)

    # Foreign key linking the notification to a user
    # This assumes notifications are primarily for users.
    # For host-specific notifications, you might link to a hosts table
    # or use a polymorphic approach if notifications can be for Users or Hosts.
    # Based on the knowledge base, linking to users is standard.
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # The content of the notification message
    # VARCHAR(255) limits the message length to 255 characters
    message = db.Column(db.String(255), nullable=False)

    # Flag to indicate if the notification has been read by the recipient
    # Default is False, meaning it's unread when created
    is_read = db.Column(db.Boolean, default=False, nullable=False)

    # Timestamp of when the notification was created
    # Default is the current UTC time when the record is created
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    # --- End Column Definitions ---

    # --- Relationship Definitions ---
    # Define the relationship to the User model
    # This creates a 'notifications' attribute on User instances
    # backref='notifications' creates a 'user' attribute on Notification instances
    # lazy='dynamic' means queries for notifications are not run until accessed
    # user = db.relationship('User', backref='notifications', lazy='dynamic')
    # If the User model already defines the backref, you don't need this line here.
    # The knowledge base snippet implies the backref is defined elsewhere (likely in models/user.py).
    # --- End Relationships ---

    def __repr__(self):
        """
        String representation of the Notification object.
        Useful for debugging and logging.
        """
        return f'<Notification {self.id} for User {self.user_id}: {self.message[:50]}...>' # Show first 50 chars

    # --- Helper Methods ---
    def mark_as_read(self):
        """
        Mark the notification as read.
        """
        self.is_read = True
        # Optionally, add to session and commit here if desired,
        # but it's often better to let the calling function handle the session.
        # db.session.add(self)
        # db.session.commit()

    def mark_as_unread(self):
        """
        Mark the notification as unread.
        """
        self.is_read = False
        # Optionally, add to session and commit here if desired,
        # but it's often better to let the calling function handle the session.
        # db.session.add(self)
        # db.session.commit()
    # --- End Helper Methods ---
# --- End Notification Model ---