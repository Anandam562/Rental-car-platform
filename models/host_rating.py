# models/host_rating.py
from . import db
from datetime import datetime

class HostRating(db.Model):
    __tablename__ = 'host_ratings'

    id = db.Column(db.Integer, primary_key=True)
    host_id = db.Column(db.Integer, db.ForeignKey('hosts.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    # --- CRITICAL FIX: Ensure this column is defined ---
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False) # <-- This line MUST exist
    # --- END CRITICAL FIX ---
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # --- Relationship Definitions ---
    # Relationships to Host, User, and Booking (assuming backrefs are defined in those models)
    # host = db.relationship('Host', backref='ratings') # Often defined via backref in Host model
    # user = db.relationship('User', backref='host_ratings_given') # Often defined via backref in User model
    # booking = db.relationship('Booking', backref='host_rating') # Often defined via backref in Booking model
    # --- End Relationships ---

    def __repr__(self):
        return f'<HostRating {self.rating} stars for Host {self.host_id} (Booking {self.booking_id})>'
# --- End HostRating Model ---