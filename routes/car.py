# routes/car.py
from datetime import timedelta, datetime

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import current_user, login_required
from flask_wtf import FlaskForm
from wtforms.fields.datetime import DateField
from wtforms.fields.simple import SubmitField
from wtforms.validators import DataRequired

from models import db
from models.booking import Booking
from models.car import Car
# from models.location import Location # If you still use Location model for other purposes
# Import the distance calculator utility
from utils.distance_calculator import calculate_distance
# Import requests for the Nominatim API call
import requests

from .booking import booking_bp

# Import the filter manager function
# --- CORRECTED IMPORT ---
# Ensure this path matches your actual project structure.
# Based on the conversation, filters are in routes/user/filters/
# and the manager function is apply_filters_to_query in routes/user/filters/filters.py
try:
    # Attempt relative import if filters are within the routes package structure
    from .user.filters.filters import apply_filters_to_query
except ImportError:
    # Fallback if filters are in a different structure or need absolute import
    # Adjust 'your_app_package' to your actual package name if needed
    # from your_app_package.routes.user.filters.filters import apply_filters_to_query
    # Or if filters are directly importable (e.g., added to sys.path or __init__.py)
    # Make sure this path is correct for YOUR project structure
    from routes.user.filters.filters import apply_filters_to_query
# --- END CORRECTED IMPORT ---

# Create the 'car' blueprint. The name 'car' determines the prefix for endpoint names (e.g., 'car.home')
car_bp = Blueprint('car', __name__)

class BookingInitiationForm(FlaskForm):
    """Simple form for initiating a booking (dates + CSRF)"""
    start_date = DateField('Start Date', validators=[DataRequired()])
    end_date = DateField('End Date', validators=[DataRequired()])
    submit = SubmitField('Book Now')

# --- Route for Homepage ---
# Ensure this route is defined only ONCE
@car_bp.route('/')
def home():
    """
    Display the homepage.
    This is the 'car.home' endpoint.
    """
    # If you need to pass locations or other data to the homepage template, do it here.
    # For example, if you want to show popular cities or areas:
    # locations = Location.query.order_by(Location.city, Location.name).all()
    # return render_template('home.html', locations=locations)

    # For now, just render the homepage template.
    return render_template('home.html')


# --- End Homepage Route ---

# --- Route for Car Listing/Search ---
@car_bp.route('/cars')
def car_list():
    """
    Display a list of cars.
    1. Gets location and filter parameters from the request.
    2. Builds a query and applies filters.
    3. Calculates distance and sorts.
    4. Renders the consolidated car_list.html template.
    This is the 'car.car_list' endpoint.
    """
    # --- 1. Get Location Parameters ---
    user_lat_str = request.args.get('user_lat')
    user_lng_str = request.args.get('user_lng')
    # Optional: Get radius if passed from a form input (not the slider which is max_price)
    # radius_km_str = request.args.get('radius')

    # --- 2. Validate Location ---
    if not user_lat_str or not user_lng_str:
        flash("Unable to determine your location for searching. Please use 'Detect my location' or select a suggestion on the homepage.", "warning")
        return redirect(url_for('car.home'))

    try:
        user_lat = float(user_lat_str)
        user_lng = float(user_lng_str)
        # radius_km = float(radius_km_str) if radius_km_str else None
    except (ValueError, TypeError):
        flash("Invalid location coordinates provided.", "danger")
        return redirect(url_for('car.home'))
    # --- End Validation ---

    # --- 3. Get Filter Parameters from Request ---
    # Get filter values directly from request.args (MultiDict)
    car_type_filters = request.args.getlist('type') # e.g., ['SUV', 'Hatchback']
    transmission_filters = request.args.getlist('transmission') # e.g., ['Manual']
    fuel_type_filters = request.args.getlist('fuel') # e.g., ['Petrol', 'Diesel']
    brand_filters = request.args.getlist('brand') # e.g., ['Maruti', 'Hyundai']
    feature_filters = request.args.getlist('features') # e.g., ['ac', 'gps']
    min_seats_str = request.args.get('min_seats')
    max_seats_str = request.args.get('max_seats')
    min_price_str = request.args.get('min_price')
    max_price_str = request.args.get('max_price') # This is the one from the slider/form
    min_year_str = request.args.get('min_year')
    # --- End Get Filter Parameters ---

    # --- 4. Core Query Logic (Initial Filtering) ---
    # Start with all available cars that have coordinates
    query = Car.query.filter(
        Car.is_available == True,
        Car.latitude.isnot(None),
        Car.longitude.isnot(None)
    )
    # --- End Core Query Logic ---

    # --- 5. Apply Filters Directly to Query ---
    # --- Car Type Filter ---
    if car_type_filters:
        # Define valid types to prevent arbitrary filtering
        VALID_CAR_TYPES = {'SUV', 'Hatchback', 'Sedan', 'MUV', 'Luxury', 'EV'}
        valid_selected_types = [ct for ct in car_type_filters if ct in VALID_CAR_TYPES]
        if valid_selected_types:
            query = query.filter(Car.car_type.in_(valid_selected_types))
    # --- End Car Type Filter ---

    # --- Transmission Filter ---
    if transmission_filters:
        VALID_TRANSMISSIONS = {'Manual', 'Automatic'}
        valid_selected_trans = [t for t in transmission_filters if t in VALID_TRANSMISSIONS]
        if valid_selected_trans:
            query = query.filter(Car.transmission.in_(valid_selected_trans))
    # --- End Transmission Filter ---

    # --- Fuel Type Filter ---
    if fuel_type_filters:
        VALID_FUELS = {'Petrol', 'Diesel', 'CNG', 'EV', 'Electric', 'Hybrid'}
        # Normalize values (e.g., 'Electric' -> 'EV')
        normalized_fuels = []
        for f in fuel_type_filters:
            if f in VALID_FUELS:
                norm_f = 'EV' if f.lower() in ['electric', 'ev'] else f
                normalized_fuels.append(norm_f)
        if normalized_fuels:
            query = query.filter(Car.fuel_type.in_(normalized_fuels))
    # --- End Fuel Type Filter ---

    # --- Brand Filter ---
    if brand_filters:
        # Define valid brands or fetch from a predefined list/model
        VALID_BRANDS = {'Maruti', 'Hyundai', 'Tata', 'Mahindra', 'Toyota', 'Honda', 'Ford', 'Volkswagen'}
        valid_selected_brands = [b for b in brand_filters if b in VALID_BRANDS]
        if valid_selected_brands:
            query = query.filter(Car.make.in_(valid_selected_brands))
    # --- End Brand Filter ---

    # --- Seating Capacity Filter ---
    try:
        if min_seats_str:
            min_seats = int(min_seats_str)
            query = query.filter(Car.seats >= min_seats)
        if max_seats_str:
            max_seats = int(max_seats_str)
            query = query.filter(Car.seats <= max_seats)
    except (ValueError, TypeError):
        pass # Gracefully handle invalid seat numbers
    # --- End Seating Capacity Filter ---

    # --- Price Range Filter ---
    try:
        if min_price_str:
            min_price = float(min_price_str)
            query = query.filter(Car.price_per_hour >= min_price)
        if max_price_str:
            max_price = float(max_price_str)
            query = query.filter(Car.price_per_hour <= max_price)
    except (ValueError, TypeError):
        pass # Gracefully handle invalid prices
    # --- End Price Range Filter ---

    # --- Model Year Filter ---
    try:
        if min_year_str:
            min_year = int(min_year_str)
            # Add validation for reasonable year range if needed
            MIN_VALID_YEAR = 1950
            MAX_VALID_YEAR = 2030
            if MIN_VALID_YEAR <= min_year <= MAX_VALID_YEAR:
                query = query.filter(Car.year >= min_year)
    except (ValueError, TypeError):
        pass # Gracefully handle invalid years
    # --- End Model Year Filter ---

    # --- Features Filter ---
    if feature_filters:
        # Map feature names from URL param to Car model boolean field names
        FEATURE_MAP = {
            'ac': 'has_ac',
            'bluetooth': 'has_bluetooth',
            'sunroof': 'has_sunroof',
            'gps': 'has_gps',
            'usb_port': 'has_usb_port',
            'reverse_camera': 'has_reverse_camera'
            # Add more mappings as needed, ensure Car model has these boolean fields
        }
        from sqlalchemy import and_
        filter_conditions = []
        for feature_key in feature_filters:
            if feature_key in FEATURE_MAP:
                car_field_name = FEATURE_MAP[feature_key]
                if hasattr(Car, car_field_name):
                    # Add condition: Car.car_field_name == True
                    filter_conditions.append(getattr(Car, car_field_name) == True)

        # Apply filter for each selected feature (AND logic: car must have ALL selected features)
        if filter_conditions:
            # Use * to unpack the list of conditions
            query = query.filter(and_(*filter_conditions))
    # --- End Features Filter ---
    # --- End Applying Filters Directly ---

    # --- 6. Execute Query to get candidates ---
    # Get cars that pass the basic filters and have location data
    cars = query.all()
    # --- End Execute Query ---

    # --- 7. Distance Calculation & Sorting ---
    car_distances = []
    for car in cars:
        # Calculate distance for each car
        distance = calculate_distance(
            user_lat, user_lng,
            car.latitude, car.longitude
        )
        # Round distance for display/storage
        rounded_distance = round(distance, 2)

        # Store distance on car object for template access and sorting
        car.display_distance_km = rounded_distance # Use a clear attribute name

        # Add to list for sorting (radius filter can be applied here if needed)
        # For now, we sort all cars by distance.
        car_distances.append((car, rounded_distance))

    # Sort the list by distance (nearest first)
    car_distances.sort(key=lambda x: x[1])
    # Extract sorted cars
    cars_sorted_by_distance = [car for car, distance in car_distances]
    # --- End Distance Logic ---

    # --- 8. Prepare Context for Template ---
    selected_location_display = f"Cars near you (approx. Lat: {user_lat:.4f}, Lng: {user_lng:.4f})"
    # Add user location context for template (e.g., for map, re-search)
    user_location_context = {
        'lat': user_lat,
        'lng': user_lng,
        # 'radius': radius_km # Pass if radius is used
    }

    # --- Prepare Filter Context for Template ---
    # This helps the template know which filters are active to highlight them/reset them
    active_filters_context = {
        'types': car_type_filters,
        'transmissions': transmission_filters,
        'fuels': fuel_type_filters,
        'brands': brand_filters,
        'features': feature_filters,
        'min_seats': min_seats_str,
        'max_seats': max_seats_str,
        'min_price': min_price_str,
        'max_price': max_price_str, # Pass the max price for slider
        'min_year': min_year_str,
    }
    # --- End Prepare Filter Context ---

    # --- 9. Render Consolidated Template ---
    # Pass the sorted list, context messages, user location data, and active filters
    return render_template(
        'car_list.html', # Path to your single, consolidated template
        cars=cars_sorted_by_distance, # Pass the sorted list
        selected_location_display=selected_location_display,
        user_location=user_location_context,
        active_filters=active_filters_context, # Pass active filters for UI
        # You can pass other context like total_cars, current_page, total_pages for pagination if needed later
    )
# --- End Car Listing Route ---

# --- Route for Car Detail ---
@car_bp.route('/cars/<int:car_id>')
def car_detail(car_id):
    """
    Display detailed information for a specific car.
    This is the 'car.car_detail' endpoint.
    """
    # --- Get the car object or return 404 if not found ---
    # Assuming Car stores location details directly
    car = Car.query.filter(Car.id == car_id).first_or_404()
    # --- End Get Car ---

    # --- Calculate Default Dates ---
    # Calculate default start date (e.g., tomorrow)
    default_start_date = datetime.today().date() + timedelta(days=1)
    # Calculate default end date (e.g., day after tomorrow)
    default_end_date = default_start_date + timedelta(days=1)
    # --- End Calculate Dates ---

    # --- CRITICAL FIX: Instantiate and Pass Form ---
    # Create an instance of the booking form
    form = BookingInitiationForm()
    # Pre-populate form with default dates if needed (optional)
    # form.start_date.data = default_start_date
    # form.end_date.data = default_end_date
    # --- END CRITICAL FIX ---

    # --- Render Template with Context ---
    # Pass the car object and default dates
    return render_template(
        'car_detail.html',
        car=car,
        default_start_date=default_start_date, # <-- Pass default_start_date
        default_end_date=default_end_date,      # <-- Pass default_end_date (good to have)
        form = form  # <-- Pass the form instance
    )


# --- Route for Address Suggestions (API) ---
@car_bp.route('/suggest')
def suggest_address():
    """
    Provides address suggestions based on user input using Nominatim.
    This is the 'car.suggest_address' endpoint.
    """
    query = request.args.get('q', '').strip()
    if len(query) < 2:
        return jsonify([])

    # Use Nominatim API for suggestions
    # --- CRITICAL FIX 2: Corrected URL (no extra spaces) ---
    # BEFORE (Incorrect):
    # url = "https://nominatim.openstreetmap.org/search  "
    # AFTER (Correct):
    url = "https://nominatim.openstreetmap.org/search" # Use the corrected constant defined above
    # --- END CRITICAL FIX 2 ---
    params = {
        'q': query,
        'format': 'json',
        'countrycodes': 'IN', # Restrict to India
        'addressdetails': 1, # Get detailed address parts
        'limit': 10 # Limit results
    }
    # Nominatim requires a User-Agent header
    headers = {'User-Agent': 'ZoomCarClone/1.0 (contact@yourapp.com)'}

    try:
        response = requests.get(url, params=params, headers=headers, timeout=5)
        response.raise_for_status() # Raise an exception for bad status codes (4xx, 5xx)
        data = response.json()
        results = []
        for item in data:
            addr = item.get('address', {})
            # --- Improved field mapping ---
            # Nominatim keys can vary, try common ones for locality/sub-area
            locality_parts = [
                addr.get('suburb'),
                addr.get('neighbourhood'), # UK spelling
                addr.get('neighborhood'), # US spelling
                addr.get('hamlet'),
                addr.get('residential'),
                addr.get('quarter') # Sometimes used in cities
            ]
            # Get the first non-empty value from the list
            locality = next((part for part in locality_parts if part), None)

            # Get city/town/village
            city = addr.get('city') or addr.get('town') or addr.get('village')

            # Get state
            state = addr.get('state')

            # Get postcode
            postcode = addr.get('postcode')

            # Get road/street
            road = addr.get('road') or addr.get('pedestrian')

            # Get house number
            house_number = addr.get('house_number')
            # --- End Improved Mapping ---

            results.append({
                'display_name': item['display_name'],
                'lat': float(item['lat']),
                'lon': float(item['lon']),
                # Map Nominatim keys to potential fields you might use
                'road': road,
                'house_number': house_number,
                'postcode': postcode,
                'city': city,
                'state': state,
                'locality': locality, # Best guess for locality/area
                'county': addr.get('county') or addr.get('district') # District/County
                # Add more fields if needed from Nominatim response (e.g., country)
            })
        return jsonify(results)
    except requests.exceptions.RequestException as e:
        # Handle network errors, timeouts, HTTP errors
        print(f"Suggestion API error (Request): {e}")
        return jsonify({'error': 'Failed to fetch suggestions (Network Error)'}), 500
    except ValueError as e: # Includes JSONDecodeError
        # Handle errors parsing JSON response
        print(f"Suggestion API error (JSON): {e}")
        return jsonify({'error': 'Failed to process suggestions (Data Error)'}), 500
    except Exception as e:
        # Handle other unexpected errors
        print(f"Unexpected error in suggest_address: {e}")
        return jsonify({'error': 'An unexpected error occurred'}), 500
# --- End Address Suggestions Route ---



