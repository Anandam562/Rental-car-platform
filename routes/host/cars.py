from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms.fields.choices import SelectField
from wtforms.fields.numeric import IntegerField, FloatField
from wtforms.fields.simple import StringField, TextAreaField, BooleanField, SubmitField, FileField
from wtforms.validators import DataRequired, NumberRange, Optional

from . import host_bp
from models import db
from models.host import Host
from models.car import Car
from models.car_image import CarImage
from models.location import Location
from werkzeug.utils import secure_filename
import os
from models.location import Location # <-- Add this import
import requests # For Nominatim API call


@host_bp.route('/cars')
@login_required
def list_cars():
    """List all cars owned by host"""
    host = Host.query.filter_by(user_id=current_user.id).first()
    if not host:
        flash('Please complete your host profile first')
        return redirect(url_for('host.setup_profile'))

    cars = Car.query.filter_by(host_id=host.id).all()
    return render_template('host/cars/list.html', cars=cars, host=host)


# --- CRITICAL FIX: Define Car Form using WTForms ---
class CarForm(FlaskForm):
    """WTForm for Car (Add/Edit)"""
    make = StringField('Make', validators=[DataRequired()])
    model = StringField('Model', validators=[DataRequired()])
    year = IntegerField('Year', validators=[DataRequired(), NumberRange(min=1900, max=2030)])
    price_per_hour = FloatField('Price per Hour (₹)', validators=[DataRequired(), NumberRange(min=0)])
    color = StringField('Color', validators=[Optional()])
    mileage = IntegerField('Mileage (km)', validators=[Optional(), NumberRange(min=0)])
    fuel_type = SelectField('Fuel Type', choices=[('', 'Select Fuel Type'), ('Petrol', 'Petrol'), ('Diesel', 'Diesel'), ('CNG', 'CNG'), ('EV', 'EV'), ('Electric', 'Electric'), ('Hybrid', 'Hybrid')], validators=[DataRequired()])
    transmission = SelectField('Transmission', choices=[('', 'Select Transmission'), ('Manual', 'Manual'), ('Automatic', 'Automatic')], validators=[DataRequired()])
    seats = IntegerField('Seats', validators=[DataRequired(), NumberRange(min=1, max=20)])
    # Location fields (will be handled by JavaScript/hidden inputs)
    latitude = FloatField('Latitude', validators=[Optional()]) # Hidden input
    longitude = FloatField('Longitude', validators=[Optional()]) # Hidden input
    full_address = TextAreaField('Full Address', validators=[Optional()]) # Hidden/Readonly input
    street_address = StringField('Street Address', validators=[Optional()]) # Hidden/Readonly input
    locality = StringField('Locality/Area', validators=[Optional()]) # Hidden/Readonly input
    city = StringField('City', validators=[DataRequired()]) # Required
    state = StringField('State', validators=[DataRequired()]) # Required
    pincode = StringField('Pincode', validators=[Optional()]) # Hidden/Readonly input
    is_available = BooleanField('Available for booking')
    images = FileField('Car Images', validators=[Optional()])
    submit = SubmitField('Add Car') # Or 'Update Car' based on context

# --- END CRITICAL FIX ---

@host_bp.route('/cars/add', methods=['GET', 'POST'])
@login_required
def add_car():
    """Add new car"""
    host = Host.query.filter_by(user_id=current_user.id).first_or_404()

    # --- CRITICAL FIX: Instantiate the form ---
    form = CarForm() # Create an instance of the form
    # --- END CRITICAL FIX ---

    if form.validate_on_submit(): # This checks CSRF token and other validations
        # --- Get Location Data from Form (processed by JavaScript) ---
        latitude = form.latitude.data
        longitude = form.longitude.data
        full_address = form.full_address.data.strip()[:500] if form.full_address.data else None
        street_address = form.street_address.data.strip()[:255] if form.street_address.data else None
        locality = form.locality.data.strip()[:100] if form.locality.data else None
        city = form.city.data.strip()[:100] if form.city.data else None
        state = form.state.data.strip()[:100] if form.state.data else None
        pincode = form.pincode.data.strip()[:20] if form.pincode.data else None
        # --- End Get Location Data ---

        # --- Validate Location Data ---
        if not latitude or not longitude or not city or not state:
            flash('Location details (coordinates, city, state) are required.', 'danger')
            return render_template('host/cars/add.html', form=form) # Pass form back with errors
        # --- End Validation ---

        # --- Create Car Object ---
        try:
            car = Car(
                make=form.make.data.strip(),
                model=form.model.data.strip(),
                year=form.year.data,
                price_per_hour=form.price_per_hour.data,
                color=form.color.data.strip() if form.color.data else None,
                mileage=form.mileage.data or 0,
                fuel_type=form.fuel_type.data,
                transmission=form.transmission.data,
                seats=form.seats.data,
                # --- Assign Location Data ---
                latitude=latitude,
                longitude=longitude,
                full_address=full_address,
                street_address=street_address,
                locality=locality,
                city=city,
                state=state,
                pincode=pincode,
                # --- End Assign Location Data ---
                host_id=host.id,
                is_available=form.is_available.data
            )

            db.session.add(car)
            db.session.flush() # Get car ID for image filenames

            # Handle image uploads
            if 'images' in request.files:
                files = request.files.getlist('images')
                for i, file in enumerate(files):
                    if file and file.filename != '':
                        filename = secure_filename(file.filename)
                        name, ext = os.path.splitext(filename)
                        # Include car ID in filename
                        filename = f"{name}_{car.id}_{i}{ext}"
                        filepath = os.path.join('static', 'uploads', filename)
                        # Ensure the uploads directory exists
                        os.makedirs(os.path.dirname(filepath), exist_ok=True)
                        file.save(filepath)

                        car_image = CarImage(
                            filename=filename,
                            car_id=car.id,
                            is_primary=(i == 0)
                        )
                        db.session.add(car_image)

            db.session.commit()
            flash('Car added successfully!', 'success')
            return redirect(url_for('host.list_cars'))

        except Exception as e:
            db.session.rollback()
            print(f"Error adding car: {e}") # Log the error
            flash(f'Error adding car: {str(e)}', 'danger')
            return render_template('host/cars/add.html', form=form) # Pass form back with errors

    # For GET request or failed validation, render the form
    # Pre-populate form with request data if available (for errors)
    # locations = Location.query.order_by(Location.city, Location.name).all() # If needed for other dropdowns
    return render_template('host/cars/add.html', form=form) # Pass the form instance

@host_bp.route('/cars/<int:car_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_car(car_id):
    """Edit existing car"""
    host = Host.query.filter_by(user_id=current_user.id).first_or_404()
    car = Car.query.get_or_404(car_id)

    # Check if host owns this car
    if car.host_id != host.id:
        flash('Access denied.')
        return redirect(url_for('host.list_cars'))

    # --- CRITICAL FIX: Instantiate the form and populate with car data ---
    form = CarForm(obj=car) # Populate form with existing car data
    # --- END CRITICAL FIX ---

    if form.validate_on_submit(): # This checks CSRF token and other validations
        # --- Get Updated Location Data from Form (processed by JavaScript) ---
        latitude = form.latitude.data
        longitude = form.longitude.data
        full_address = form.full_address.data.strip()[:500] if form.full_address.data else None
        street_address = form.street_address.data.strip()[:255] if form.street_address.data else None
        locality = form.locality.data.strip()[:100] if form.locality.data else None
        city = form.city.data.strip()[:100] if form.city.data else None
        state = form.state.data.strip()[:100] if form.state.data else None
        pincode = form.pincode.data.strip()[:20] if form.pincode.data else None
        # --- End Get Updated Location Data ---

        # --- Validate Location Data ---
        if not latitude or not longitude or not city or not state:
            flash('Location details (coordinates, city, state) are required.', 'danger')
            return render_template('host/cars/edit.html', form=form, car=car) # Pass form and car back
        # --- End Validation ---

        # --- Update Car Object ---
        try:
            car.make = form.make.data.strip()
            car.model = form.model.data.strip()
            car.year = form.year.data
            car.price_per_hour = form.price_per_hour.data
            car.color = form.color.data.strip() if form.color.data else None
            car.mileage = form.mileage.data or 0
            car.fuel_type = form.fuel_type.data
            car.transmission = form.transmission.data
            car.seats = form.seats.data
            # --- Update Location Data ---
            car.latitude = latitude
            car.longitude = longitude
            car.full_address = full_address
            car.street_address = street_address
            car.locality = locality
            car.city = city
            car.state = state
            car.pincode = pincode
            # --- End Update Location Data ---
            car.is_available = form.is_available.data

            # Handle new image uploads (if any)
            if 'images' in request.files:
                files = request.files.getlist('images')
                for i, file in enumerate(files):
                    if file and file.filename != '':
                        filename = secure_filename(file.filename)
                        name, ext = os.path.splitext(filename)
                        # Include car ID in filename
                        filename = f"{name}_{car.id}_{len(car.images) + i}{ext}" # Append to existing count
                        filepath = os.path.join('static', 'uploads', filename)
                        os.makedirs(os.path.dirname(filepath), exist_ok=True)
                        file.save(filepath)

                        car_image = CarImage(
                            filename=filename,
                            car_id=car.id
                            # is_primary not set here, user can set it later or logic can assign
                        )
                        db.session.add(car_image)

            db.session.commit()
            flash('Car updated successfully!', 'success')
            return redirect(url_for('host.list_cars'))

        except Exception as e:
            db.session.rollback()
            print(f"Error updating car: {e}")
            flash(f'Error updating car: {str(e)}', 'danger')
            return render_template('host/cars/edit.html', form=form, car=car) # Pass form and car back

    # For GET request, render the form with pre-populated data
    return render_template('host/cars/edit.html', form=form, car=car) # Pass the form and car instance

# ... (rest of routes/host/cars.py - delete_car, delete_car_image, etc.) ...

@host_bp.route('/cars/<int:car_id>/delete')
@login_required
def delete_car(car_id):
    """Delete car"""
    host = Host.query.filter_by(user_id=current_user.id).first()
    car = Car.query.get_or_404(car_id)

    # Check if host owns this car
    if car.host_id != host.id:
        flash('Access denied')
        return redirect(url_for('host.list_cars'))

    # Delete associated images
    for image in car.images:
        filepath = os.path.join('static', 'uploads', image.filename)
        if os.path.exists(filepath):
            os.remove(filepath)
        db.session.delete(image)

    db.session.delete(car)
    db.session.commit()
    flash('Car deleted successfully!')
    return redirect(url_for('host.list_cars'))


@host_bp.route('/cars/image/<int:image_id>/delete')
@login_required
def delete_car_image(image_id):
    """Delete specific car image"""
    from models.car_image import CarImage

    host = Host.query.filter_by(user_id=current_user.id).first()
    image = CarImage.query.get_or_404(image_id)
    car = image.car

    # Check if host owns this car
    if car.host_id != host.id:
        flash('Access denied')
        return redirect(url_for('host.list_cars'))

    # Delete file
    filepath = os.path.join('static', 'uploads', image.filename)
    if os.path.exists(filepath):
        os.remove(filepath)

    db.session.delete(image)
    db.session.commit()
    flash('Image deleted successfully!')
    return redirect(url_for('host.edit_car', car_id=car.id))