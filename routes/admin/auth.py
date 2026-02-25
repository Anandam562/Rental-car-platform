# routes/admin/auth.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from . import admin_bp
from models import db
from models.admin import Admin
# --- CRITICAL FIX 1: Import WTForms ---
from forms.admin import AdminLoginForm, AdminRegistrationForm  # <-- Import forms


# --- END CRITICAL FIX 1 ---

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Admin login page.
    This is the 'admin.login' endpoint.
    """
    # Redirect if already logged in as admin
    if current_user.is_authenticated and hasattr(current_user, 'access_level'):
        return redirect(url_for('admin.dashboard'))

    # --- CRITICAL FIX 2: Instantiate the AdminLoginForm ---
    form = AdminLoginForm()  # Create an instance of the form
    # --- END CRITICAL FIX 2 ---

    if request.method == 'POST':
        # --- CRITICAL FIX 3: Use form validation ---
        if form.validate_on_submit():  # This checks CSRF token and other validations
            username = form.username.data.strip()
            password = form.password.data
            # --- CRITICAL FIX 4: Get remember_me value from form ---
            # BEFORE (Incorrect - Used request.form.get directly)
            # remember = bool(request.form.get('remember_me'))

            # AFTER (Correct - Use form data)
            remember = form.remember_me.data  # <-- Get value from form object
            # --- END CRITICAL FIX 4 ---

            admin = Admin.query.filter_by(username=username).first()

            # Check if admin exists, password is correct, and admin is active
            if admin and admin.check_password(password) and admin.is_active:
                login_user(admin, remember=remember)  # <-- Pass remember value to login_user
                flash('Logged in successfully as admin.', 'success')
                # Redirect to next page or admin dashboard
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('admin.dashboard'))
            else:
                flash('Login failed. Please check your username and password, and ensure your account is active.',
                      'danger')
        else:
            # Form validation failed (CSRF, missing fields, etc.)
            flash('Please check your input and try again.', 'danger')
        # --- END CRITICAL FIX 3 ---

    # For GET request or failed validation, render the form
    # --- CRITICAL FIX 5: Pass the form instance to the template ---
    return render_template('admin/login.html', form=form)  # <-- Pass the form instance


@admin_bp.route('/logout')
@login_required
def logout():
    """Admin logout"""
    # Optional: Add authorization check to ensure only admins can logout via this route
    # if not isinstance(current_user, Admin):
    #     flash('Access denied.')
    #     return redirect(url_for('car.home'))

    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('admin.login'))  # Redirect to admin login page

# --- CRITICAL FIX 3: Add Admin Registration Route (for super admins) ---
@admin_bp.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    """Admin registration page (accessible only by super admins)"""
    # Authorization check (ensure user is a super admin)
    if not (hasattr(current_user, 'access_level') and current_user.can_manage_admins()):
        flash('Access denied. Only super admins can create new admins.')
        return redirect(url_for('admin.dashboard'))

    form = AdminRegistrationForm()  # <-- Instantiate the registration form

    if form.validate_on_submit():  # <-- This checks CSRF token and other validations
        username = form.username.data.strip()
        email = form.email.data.strip().lower()
        password = form.password.data
        confirm_password = form.confirm_password.data
        access_level = form.access_level.data
        is_active = form.is_active.data

        # Validate password confirmation
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('admin/register.html', form=form)

        # Check if admin already exists
        if Admin.query.filter_by(username=username).first() or Admin.query.filter_by(email=email).first():
            flash('Username or email already taken by another admin.', 'danger')
            return render_template('admin/register.html', form=form)

        # Create new admin
        new_admin = Admin(
            username=username,
            email=email,
            access_level=access_level,
            is_active=is_active
        )
        new_admin.set_password(password)
        db.session.add(new_admin)

        try:
            db.session.commit()
            flash(f'Admin {username} created successfully!', 'success')
            return redirect(url_for('admin.list_admins'))  # Redirect to admin list
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating admin: {str(e)}', 'danger')
            return render_template('admin/register.html', form=form)

    # For GET request or failed validation, render the form
    return render_template('admin/register.html', form=form)
# --- END CRITICAL FIX 3 ---
