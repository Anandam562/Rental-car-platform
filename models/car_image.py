# models/car_image.py
from . import db
from datetime import datetime

class CarImage(db.Model):
    __tablename__ = 'car_images'

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    car_id = db.Column(db.Integer, db.ForeignKey('cars.id'), nullable=False)
    is_primary = db.Column(db.Boolean, default=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    # --- Relationship Definitions ---
    # DO NOT DEFINE 'car' relationship here.
    # It is provided automatically by the 'backref' defined in the Car model.
    # - Car.images backref='car' creates a 'car' attribute on CarImage.
    # --- End Relationships ---

    def __repr__(self):
        return f'<CarImage {self.filename} (Car ID: {self.car_id})>'
