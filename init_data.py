from app import app
from models import db
from models.location import Location
from models.user import User
from models.car import Car
from models.car_image import CarImage
from models.booking import Booking


def create_sample_data():
    with app.app_context():
        # Clear existing data
        db.drop_all()
        db.create_all()

        # Create sample locations
        locations = [
            Location(name='Indiranagar', city='Bangalore', address='Indiranagar, Bangalore', latitude=12.9716,
                     longitude=77.5946),
            Location(name='Koramangala', city='Bangalore', address='Koramangala, Bangalore', latitude=12.9352,
                     longitude=77.6245),
            Location(name='Whitefield', city='Bangalore', address='Whitefield, Bangalore', latitude=12.9725,
                     longitude=77.7236)
        ]

        for location in locations:
            db.session.add(location)

        # Create sample user
        user = User(username='testuser', email='test@example.com', phone='1234567890')
        user.set_password('password')
        db.session.add(user)

        # Create sample cars
        cars = [
            Car(make='Toyota', model='Innova', year=2022, price_per_day=2500, color='White', mileage=15000,
                fuel_type='Petrol', transmission='Manual', seats=7, location_id=1),
            Car(make='Hyundai', model='Creta', year=2023, price_per_day=1800, color='Blue', mileage=8000,
                fuel_type='Petrol', transmission='Automatic', seats=5, location_id=2),
            Car(make='Maruti', model='Swift', year=2021, price_per_day=1200, color='Red', mileage=22000,
                fuel_type='Petrol', transmission='Manual', seats=5, location_id=3)
        ]

        for car in cars:
            db.session.add(car)

        db.session.commit()
        print("Sample data created successfully!")


if __name__ == '__main__':
    create_sample_data()