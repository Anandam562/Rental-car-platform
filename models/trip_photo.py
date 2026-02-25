# models/trip_photo.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from models import db
from datetime import datetime

class TripPhoto(db.Model):
    __tablename__ = 'trip_photos'

    id = Column(Integer, primary_key=True)
    booking_id = Column(Integer, db.ForeignKey('bookings.id'), nullable=False)
    photo_path = Column(String(255), nullable=False) # Store the path relative to upload folder
    upload_type = Column(String(20), nullable=False) # 'start' or 'end'
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    booking = relationship('Booking', back_populates='trip_photos') # Assuming a backref exists in Booking

    def __repr__(self):
        return f'<TripPhoto {self.id} for Booking {self.booking_id} ({self.upload_type})>'