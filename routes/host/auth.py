

# routes/host/auth.py (Relevant part - register function)
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
# --- CRITICAL FIX 1: Import WTForms ---
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, TelField, SubmitField, HiddenField
from wtforms.fields.simple import BooleanField
from wtforms.validators import DataRequired, Email, Length, Optional
# --- END CRITICAL FIX 1 ---
from . import host_bp
from models import db
from models.user import User
from models.host import Host


# --- CRITICAL FIX 2: Define Host Registration Form using WTForms ---
class HostRegistrationForm(FlaskForm):
    """WTForm for Host registration"""
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired()])
    company_name = StringField('Company Name / Your Name', validators=[DataRequired(), Length(max=100)])
    phone = TelField('Phone Number', validators=[DataRequired(), Length(min=10, max=20)])
    address = TextAreaField('Address', validators=[Optional(), Length(max=500)])
    # Hidden fields for location coordinates (if needed from previous step)
    latitude = HiddenField('Latitude')
    longitude = HiddenField('Longitude')
    full_address = HiddenField('Full Address')
    street_address = HiddenField('Street Address')
    locality = HiddenField('Locality')
    city = HiddenField('City')
    state = HiddenField('State')
    pincode = HiddenField('Pincode')
    submit = SubmitField('Register as Host')

# --- CRITICAL FIX 2: Define HostLoginForm using WTForms ---
class HostLoginForm(FlaskForm):
    """WTForm for host login"""
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Login as Host')
# --- END CRITICAL FIX 2 ---

@host_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    Host registration page.
    This is the 'host.register' endpoint.
    """
    # --- CRITICAL FIX 3: Instantiate the form ---
    form = HostRegistrationForm()  # Create an instance of the form
    # --- END CRITICAL FIX 3 ---

    # Pre-fill email if provided in query string (e.g., from user login)
    prefill_email = request.args.get('email', '')

    if request.method == 'POST':
        # --- CRITICAL FIX 4: Use form validation ---
        # BEFORE (Manual validation)
        # email = request.form.get('email')
        # password = request.form.get('password')
        # confirm_password = request.form.get('confirm_password')
        # company_name = request.form.get('company_name')
        # phone = request.form.get('phone')
        # address = request.form.get('address')

        # AFTER (WTForms validation)
        if form.validate_on_submit():  # This checks CSRF token and other validations
            email = form.email.data.strip().lower()
            password = form.password.data
            confirm_password = form.confirm_password.data
            company_name = form.company_name.data.strip()
            phone = form.phone.data.strip()
            address = form.address.data.strip() if form.address.data else ''

            # --- Get Location Data from Form (if collected in previous step) ---
            latitude_str = form.latitude.data
            longitude_str = form.longitude.data
            full_address = form.full_address.data
            street_address = form.street_address.data
            locality = form.locality.data
            city = form.city.data
            state = form.state.data
            pincode = form.pincode.data
            # --- End Get Location Data ---

            # --- Validate Password Confirmation ---
            if password != confirm_password:
                flash('Passwords do not match.', 'danger')
                return render_template('host/register.html', form=form, prefill_email=prefill_email)
            # --- End Password Validation ---

            # --- Check for Existing User/Host ---
            user = User.query.filter_by(email=email).first()
            if user and user.host_profile:
                flash('An account with this email is already registered as a host.', 'danger')
                return render_template('host/register.html', form=form, prefill_email=prefill_email)

            # If user exists but doesn't have a host profile, we can use that user
            # Otherwise, create a new user
            if not user:
                user = User(email=email, username=email.split('@')[0])  # Create username from email prefix
                user.set_password(password)
                db.session.add(user)
                db.session.flush()  # Get user ID without committing

            # Check if a host profile already exists for this user (shouldn't happen, but double-check)
            if not user.host_profile:
                # --- Create Host Profile with Location ---
                try:
                    latitude = float(latitude_str) if latitude_str else None
                    longitude = float(longitude_str) if longitude_str else None
                except (ValueError, TypeError):
                    latitude = None
                    longitude = None

                host = Host(
                    user_id=user.id,
                    company_name=company_name,
                    phone=phone,
                    address=address,
                    # --- Assign Location Data ---
                    latitude=latitude,
                    longitude=longitude,
                    full_address=full_address[:500] if full_address else None,
                    street_address=street_address[:255] if street_address else None,
                    locality=locality[:100] if locality else None,
                    city=city[:100] if city else None,
                    state=state[:100] if state else None,
                    pincode=pincode[:20] if pincode else None,
                    # --- End Assign Location Data ---
                    is_verified=False  # Default to not verified
                )
                db.session.add(host)
                # --- End Create Host Profile ---

                try:
                    db.session.commit()
                    flash('Host registration successful! Please log in.', 'success')
                    return redirect(url_for('host.login'))
                except Exception as e:
                    db.session.rollback()
                    print(f"Error adding host: {e}")  # Log the specific error
                    flash('Registration failed. Please try again.', 'danger')
                    return render_template('host/register.html', form=form,
                                           prefill_email=prefill_email)  # Pass form back with errors
            else:
                flash('You already have a host profile.', 'info')
                # Log them in automatically?
                login_user(user)
                return redirect(url_for('host.dashboard'))
        else:
            # Form validation failed (CSRF, missing fields, etc.)
            flash('Please correct the errors in the form.', 'danger')
        # --- END WTForms Validation ---

    # For GET request or failed validation, render the form
    # Pre-populate form with request data if available (for errors or prefill)
    if prefill_email and not form.email.data:
        form.email.data = prefill_email
    return render_template('host/register.html', form=form, prefill_email=prefill_email)  # <-- Pass the form instance

# --- END CRITICAL FIX 2 ---

@host_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Host login page.
    This is the 'host.login' endpoint.
    """
    # --- CRITICAL FIX 3: Redirect if already logged in as host ---
    # Check if user is already authenticated and has a host profile
    if current_user.is_authenticated:
        host_profile = getattr(current_user, 'host_profile', None)
        if host_profile:
            flash("You are already logged in as a host.", "info")
            return redirect(url_for('host.dashboard'))
        else:
            # Logged in as regular user, not host
            flash("You are logged in as a customer. Please logout first.", "warning")
            return redirect(url_for('car.home'))  # Or redirect to user dashboard if you have one
    # --- END CRITICAL FIX 3 ---

    # --- CRITICAL FIX 4: Instantiate the HostLoginForm ---
    form = HostLoginForm()  # Create an instance of the form
    # --- END CRITICAL FIX 4 ---

    if request.method == 'POST':
        # --- CRITICAL FIX 5: Use form validation ---
        # BEFORE (Manual validation)
        # email = request.form['email']
        # password = request.form['password']
        # remember = bool(request.form.get('remember_me'))
        #
        # user = User.query.filter_by(email=email).first()
        #
        # # Check if user exists, password is correct, and user HAS a host profile
        # if user and user.check_password(password):
        #     # Check if this user has a host profile created
        #     host_profile = getattr(user, 'host_profile', None)
        #     if host_profile:
        #         login_user(user, remember=remember)
        #         flash('Logged in successfully as host.', 'success')
        #         # Redirect to next page or host dashboard
        #         next_page = request.args.get('next')
        #         return redirect(next_page) if next_page else redirect(url_for('host.dashboard'))
        #     else:
        #         flash('This account is not registered as a host. Please register as a host first or login as a customer.')
        # else:
        #     flash('Login failed. Please check your email and password.')

        # AFTER (WTForms validation)
        if form.validate_on_submit():  # This checks CSRF token and other validations
            email = form.email.data.strip().lower()
            password = form.password.data
            remember = form.remember_me.data

            user = User.query.filter_by(email=email).first()

            # Check if user exists, password is correct, and user HAS a host profile
            if user and user.check_password(password):
                # Check if this user has a host profile created
                host_profile = getattr(user, 'host_profile', None)
                if host_profile:
                    login_user(user, remember=remember)
                    flash('Logged in successfully as host.', 'success')
                    # Redirect to next page or host dashboard
                    next_page = request.args.get('next')
                    return redirect(next_page) if next_page else redirect(url_for('host.dashboard'))
                else:
                    flash(
                        'This account is not registered as a host. Please register as a host first or login as a customer.',
                        'warning')
            else:
                flash('Login failed. Please check your email and password.', 'danger')
        else:
            # Form validation failed (CSRF, missing fields, etc.)
            flash('Please check your input and try again.', 'danger')
        # --- END CRITICAL FIX 5 ---

    # For GET request or failed validation, render the form
    # Pass the form instance to the template
    return render_template('host/login.html', form=form)  # <-- Pass the form instance


@host_bp.route('/logout')
@login_required
def logout():
    """Host logout"""
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('car.home')) # Redirect to main home page after logout

# Optional: If you want a host registration route
# @host_bp.route('/register', methods=['GET', 'POST'])
# def register():
#     # Implementation for host registration
#     # This would involve creating a User (if new) and then a Host profile linked to that user
#     pass