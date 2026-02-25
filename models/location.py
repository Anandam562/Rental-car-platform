# models/location.py
# This file exists if you have a separate 'locations' table.
# However, based on your recent Car model, you are storing location directly in Car.
# If you are NOT using a separate locations table anymore, you can leave this file minimal
# or remove references to it. If you ARE using it, define it like this:

from . import db
from datetime import datetime

class Location(db.Model):
    """
    Model for predefined pickup/dropoff locations.
    Only use this if you are linking Cars to a central locations table.
    If Car stores address details directly, this model might not be actively used
    for car listings, but could be used for administrative purposes.
    """
    __tablename__ = 'locations'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False) # e.g., "Indiranagar Store"
    city = db.Column(db.String(50), nullable=False)  # e.g., "Bangalore"
    address = db.Column(db.Text)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # --- Relationship Definitions ---
    # If you were linking Cars to Location via location_id FK in Car:
    # cars = db.relationship('Car', backref='location', lazy=True)
    # --- End Relationships ---

    def __repr__(self):
        return f'<Location {self.name}, {self.city}>'
