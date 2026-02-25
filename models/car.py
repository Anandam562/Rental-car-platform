# models/car.py
from . import db
from datetime import datetime


class Car(db.Model):
    __tablename__ = 'cars'

    id = db.Column(db.Integer, primary_key=True)
    make = db.Column(db.String(100), nullable=False)
    model = db.Column(db.String(100), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    price_per_hour = db.Column(db.Float, nullable=False) # Changed from price_per_day
    color = db.Column(db.String(50))
    mileage = db.Column(db.Integer)
    fuel_type = db.Column(db.String(20))  # Petrol, Diesel, Electric
    transmission = db.Column(db.String(20))  # Manual, Automatic
    seats = db.Column(db.Integer)

    # --- Structured Address Fields ---
    # These will store the address details directly on the car
    full_address = db.Column(db.Text)  # Store the complete address string
    street_address = db.Column(db.String(255))  # e.g., "123 Main Street"
    locality = db.Column(db.String(100))  # e.g., "Koramangala"
    city = db.Column(db.String(100))  # e.g., "Bangalore"
    state = db.Column(db.String(100))  # e.g., "Karnataka"
    pincode = db.Column(db.String(20))  # e.g., "560034"
    latitude = db.Column(db.Float)  # Store coordinates
    longitude = db.Column(db.Float)  # Store coordinates
    # --- End Structured Address Fields ---

    # --- Relationships and Foreign Keys ---
    # Link to the Host who owns this car
    host_id = db.Column(db.Integer, db.ForeignKey('hosts.id'), nullable=False)

    # --- CRITICAL: Ensure this foreign key and relationship are correct ---
    # If you are using a separate 'locations' table (OLD APPROACH):
    # location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=False) # <-- UNCOMMENT if using locations table
    # location = db.relationship('Location', backref='cars') # <-- UNCOMMENT if using locations table

    # If you are storing location details directly in Car (NEW APPROACH - based on previous conversation):
    # Comment out or remove the location_id FK and relationship if you are NOT using a separate locations table.
    # location_id = db.Column(db.Integer, db.ForeignKey('locations.id')) # <-- COMMENT OUT or REMOVE
    # location = db.relationship('Location', backref='cars') # <-- COMMENT OUT or REMOVE
    # --- END CRITICAL ---

    # Availability status
    is_available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_blocked = db.Column(db.Boolean, default=False)  # New: Host can block car
    blocked_reason = db.Column(db.String(255))  # New: Reason for blocking
    blocked_at = db.Column(db.DateTime)  # New: When blocked

    # --- Relationship Definitions ---
    # Relationship to Host: One Host can have many Cars.
    host = db.relationship('Host', backref='cars_managed')

    # Relationship to CarImage: One Car can have many Images.
    images = db.relationship('CarImage', backref='car', cascade='all, delete-orphan', lazy=True)

    # Relationship to Booking: One Car can have many Bookings.
    bookings = db.relationship('Booking', backref='car', lazy=True, cascade="all, delete-orphan")

    # --- End Relationships ---

    def __repr__(self):
        return f'<Car {self.make} {self.model}>'

    def to_dict(self):
        """Helper method to convert car object to dictionary, useful for APIs."""
        return {
            'id': self.id,
            'make': self.make,
            'model': self.model,
            'year': self.year,
            'price_per_day': self.price_per_day,
            'color': self.color,
            'mileage': self.mileage,
            'fuel_type': self.fuel_type,
            'transmission': self.transmission,
            'seats': self.seats,
            'full_address': self.full_address,
            'street_address': self.street_address,
            'locality': self.locality,
            'city': self.city,
            'state': self.state,
            'pincode': self.pincode,
            'latitude': self.latitude,
            'longitude': self.longitude,
            # Add other fields as needed for API responses
        }

    def can_be_booked(self):
        """Check if car is available for booking."""
        return self.is_available and not self.is_blocked
    # ... rest of model ...