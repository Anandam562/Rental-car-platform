from flask import Blueprint, jsonify, request
from models import db
from models.car import Car
from models.location import Location
from models.booking import Booking
from utils.distance_calculator import calculate_distance
from datetime import datetime

api_bp = Blueprint('api', __name__)


@api_bp.route('/cars')
def api_cars():
    """Get all available cars with optional filters"""
    location_id = request.args.get('location_id', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    # Base query for available cars
    query = Car.query.filter_by(is_available=True)

    # Apply location filter
    if location_id:
        query = query.filter_by(location_id=location_id)

    cars = query.all()

    # Convert to JSON
    cars_data = []
    for car in cars:
        car_dict = {
            'id': car.id,
            'make': car.make,
            'model': car.model,
            'year': car.year,
            'price_per_day': car.price_per_day,
            'color': car.color,
            'mileage': car.mileage,
            'fuel_type': car.fuel_type,
            'transmission': car.transmission,
            'seats': car.seats,
            'location': {
                'id': car.location.id,
                'name': car.location.name,
                'city': car.location.city,
                'latitude': car.location.latitude,
                'longitude': car.location.longitude
            },
            'images': [{'filename': img.filename, 'is_primary': img.is_primary} for img in car.images]
        }
        cars_data.append(car_dict)

    return jsonify(cars_data)


@api_bp.route('/locations')
def api_locations():
    """Get all locations"""
    locations = Location.query.all()
    locations_data = []

    for location in locations:
        locations_data.append({
            'id': location.id,
            'name': location.name,
            'city': location.city,
            'address': location.address,
            'latitude': location.latitude,
            'longitude': location.longitude
        })

    return jsonify(locations_data)


@api_bp.route('/search')
def api_search():
    """Search cars with location and date filters"""
    location_id = request.args.get('location_id', type=int)
    lat = request.args.get('lat', type=float)
    lng = request.args.get('lng', type=float)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    # Base query
    query = Car.query.filter_by(is_available=True)

    # Apply filters
    if location_id:
        query = query.filter_by(location_id=location_id)

    cars = query.all()

    # Add distance calculation if coordinates provided
    if lat and lng:
        for car in cars:
            car.distance = calculate_distance(
                lat, lng,
                car.location.latitude, car.location.longitude
            )
        # Sort by distance
        cars.sort(key=lambda x: getattr(x, 'distance', float('inf')))

    # Convert to JSON with distance info
    cars_data = []
    for car in cars:
        car_dict = {
            'id': car.id,
            'make': car.make,
            'model': car.model,
            'year': car.year,
            'price_per_day': car.price_per_day,
            'distance': getattr(car, 'distance', None),
            'location': {
                'name': car.location.name,
                'city': car.location.city
            },
            'primary_image': car.images[0].filename if car.images else None
        }
        cars_data.append(car_dict)

    return jsonify(cars_data)


@api_bp.route('/car/<int:car_id>')
def api_car_detail(car_id):
    """Get detailed car information"""
    car = Car.query.get_or_404(car_id)

    car_data = {
        'id': car.id,
        'make': car.make,
        'model': car.model,
        'year': car.year,
        'price_per_day': car.price_per_day,
        'color': car.color,
        'mileage': car.mileage,
        'fuel_type': car.fuel_type,
        'transmission': car.transmission,
        'seats': car.seats,
        'is_available': car.is_available,
        'location': {
            'id': car.location.id,
            'name': car.location.name,
            'city': car.location.city,
            'address': car.location.address,
            'latitude': car.location.latitude,
            'longitude': car.location.longitude
        },
        'images': [{'filename': img.filename, 'is_primary': img.is_primary} for img in car.images],
        'specifications': {
            'engine': '1.5L',
            'ac': True,
            'music_system': True,
            'airbags': 2
        }
    }

    return jsonify(car_data)


@api_bp.route('/bookings', methods=['POST'])
def api_create_booking():
    """Create booking via API"""
    data = request.get_json()

    # Validate required fields
    required_fields = ['car_id', 'start_date', 'end_date', 'user_id']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400

    car_id = data['car_id']
    user_id = data['user_id']
    start_date_str = data['start_date']
    end_date_str = data['end_date']

    # Convert dates
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

    # Validate dates
    if end_date <= start_date:
        return jsonify({'error': 'End date must be after start date'}), 400

    # Check car availability
    car = Car.query.get(car_id)
    if not car or not car.is_available:
        return jsonify({'error': 'Car not available'}), 400

    # Check for existing bookings
    existing_booking = Booking.query.filter(
        Booking.car_id == car_id,
        Booking.status.in_(['pending', 'confirmed']),
        Booking.start_date < end_date,
        Booking.end_date > start_date
    ).first()

    if existing_booking:
        return jsonify({'error': 'Car is not available for the selected dates'}), 400

    # Calculate price
    total_days = (end_date - start_date).days
    total_price = total_days * car.price_per_day

    # Create booking
    booking = Booking(
        user_id=user_id,
        car_id=car_id,
        start_date=start_date,
        end_date=end_date,
        total_price=total_price,
        status='pending'
    )

    db.session.add(booking)
    db.session.commit()

    return jsonify({
        'message': 'Booking created successfully',
        'booking_id': booking.id,
        'total_price': total_price,
        'total_days': total_days
    }), 201


@api_bp.route('/user/<int:user_id>/bookings')
def api_user_bookings(user_id):
    """Get user's bookings"""
    bookings = Booking.query.filter_by(user_id=user_id).order_by(Booking.created_at.desc()).all()

    bookings_data = []
    for booking in bookings:
        bookings_data.append({
            'id': booking.id,
            'car': {
                'id': booking.car.id,
                'make': booking.car.make,
                'model': booking.car.model,
                'year': booking.car.year
            },
            'start_date': booking.start_date.isoformat(),
            'end_date': booking.end_date.isoformat(),
            'total_price': booking.total_price,
            'status': booking.status,
            'created_at': booking.created_at.isoformat()
        })

    return jsonify(bookings_data)