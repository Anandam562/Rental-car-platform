# models/photo.py
from . import db
from datetime import datetime


class Photo(db.Model):
    __tablename__ = 'photos'

    id = db.Column(db.Integer, primary_key=True)  # <-- Photo HAS its own primary key
    filename = db.Column(db.String(255), nullable=False)
    # Link to booking for pickup/dropoff association
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)  # <-- Links to Booking
    photo_type = db.Column(db.String(20), nullable=False)  # 'pickup', 'dropoff'
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    # --- Relationships ---
    # Relationship to Booking (backref creates 'photos' on Booking)
    booking = db.relationship('Booking', backref='photos')  # Assumes Booking model exists correctly

    # --- End Relationships ---

    def __repr__(self):
        return f'<Photo {self.filename} ({self.photo_type}) for Booking {self.booking_id}>'

