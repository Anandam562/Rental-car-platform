# models/host_feedback.py
from . import db
from datetime import datetime

class HostFeedback(db.Model):
    __tablename__ = 'host_feedbacks'

    id = db.Column(db.Integer, primary_key=True)
    host_id = db.Column(db.Integer, db.ForeignKey('hosts.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False) # Link to booking
    subject = db.Column(db.String(100))
    message = db.Column(db.Text, nullable=False)
    is_resolved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # --- Relationship Definitions ---
    # Relationships to Host, User, and Booking (assuming backrefs are defined in those models)
    # host = db.relationship('Host', backref='feedbacks') # Often defined via backref in Host model
    # user = db.relationship('User', backref='host_feedbacks_given') # Often defined via backref in User model
    # booking = db.relationship('Booking', backref='host_feedback') # Often defined via backref in Booking model
    # --- End Relationships ---

    def __repr__(self):
        status = "Resolved" if self.is_resolved else "Pending"
        return f'<HostFeedback {self.subject} ({status}) for Host {self.host_id} (Booking {self.booking_id})>'