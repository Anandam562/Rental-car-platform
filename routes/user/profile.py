# routes/user/profile.py
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from flask_wtf import FlaskForm # Import FlaskForm
# Remove: from wtforms.csrf.core import CSRFTokenField # No longer needed
from wtforms.fields.simple import StringField, TelField # Use TelField for phone
from wtforms.validators import ValidationError, DataRequired, \
    Email  # Import validators
from models import db # Import db if you need to commit changes

# Use the existing user blueprint from routes/user/__init__.py
# Make sure this import matches your project structure
from routes.user import user_bp

# --- CORRECTED: Define a Form with Fields and rely on FlaskForm's CSRF ---
class ProfileEditForm(FlaskForm): # INHERIT FROM FlaskForm (handles CSRF automatically)
    """A form class for editing user profile, including CSRF token."""
    # Add fields you want WTForms to handle (including validation if desired)
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = TelField('Phone') # TelField is more appropriate for phone numbers
    # Note: FlaskForm automatically adds and validates a CSRF token
    # No need to explicitly define csrf_token field
# --- END CORRECTED ---

@user_bp.route('/profile') # This decorator defines the route /user/profile
@login_required # Ensure the user is logged in to access this page
def profile():
    """
    Display the logged-in user's profile information.
    This creates the 'user.profile' endpoint.
    """
    # The 'current_user' object is provided by Flask-Login
    # It contains the details of the currently logged-in user

    # Render the profile template, passing the user object
    # This will look for templates/user/profile/view.html
    return render_template('user/profile/view.html', user=current_user)

# --- UPDATED: Route for editing profile with FlaskForm for CSRF and Validation ---
@user_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """
    Allow the user to edit their profile information.
    This creates the 'user.edit_profile' endpoint.
    """
    form = ProfileEditForm() # Instantiate the form object

    # Pre-populate form fields with current user data on GET request
    if request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.phone.data = current_user.phone

    if form.validate_on_submit(): # This validates CSRF token AND form fields
        # Get validated data directly from the form object
        new_username = form.username.data
        new_email = form.email.data
        new_phone = form.phone.data # Can be None if not provided

        # Basic validation (add more as needed)
        # WTForms validators on username/email handle basic checks like required/valid email
        # We can add custom logic here if needed, e.g., checking uniqueness in DB
        # For now, just update assuming validation passed
        current_user.username = new_username
        current_user.email = new_email
        current_user.phone = new_phone # Can be None, which is fine

        try:
            db.session.commit() # Commit the changes to the database
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('user.profile')) # Redirect back to the profile view
        except Exception as e:
            db.session.rollback() # Rollback on error
            flash(f'Error updating profile: {str(e)}', 'danger')
            # Re-render the form with errors (handled by WTForms)
            return render_template('user/profile/edit.html', user=current_user, form=form)

    # If form validation fails (including CSRF or field validation),
    # render the template again, passing the form which now contains errors
    return render_template('user/profile/edit.html', user=current_user, form=form)
# --- END UPDATED ---