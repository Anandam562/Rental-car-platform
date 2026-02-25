# routes/some_bp.py (Example - Fix the route logic)
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
# --- CRITICAL FIX 1: Import the correct model for authorization check ---
# If this route is for HOSTS, import Host
# If this route is for USERS, import User
# If this route is for ADMINS, import Admin
from models.host import Host  # <-- Assuming this route is for hosts
# --- END CRITICAL FIX 1 ---
from . import some_bp  # Replace 'some_bp' with your actual blueprint name


@some_bp.route('/some-route')
@login_required
def some_route():
    """
    Example route that requires host authorization.
    This is the 'some_bp.some_route' endpoint.
    """
    # --- CRITICAL FIX 2: Correct Authorization Check ---
    # BEFORE (Incorrect - Assumed current_user has host_profile)
    # if not current_user.host_profile: # <-- This will fail for regular users
    #     flash('Access denied.')
    #     return redirect(url_for('car.home'))

    # AFTER (Correct - Check user type and host profile)
    # Option A: Check if current_user is a Host object (if Host model inherits UserMixin)
    # if not isinstance(current_user, Host):
    #     flash('Access denied. This page is for hosts only.')
    #     return redirect(url_for('car.home'))

    # Option B: Check if current_user is a User and has a host_profile (via backref)
    # This is more common if Host is linked to User
    if not isinstance(current_user, User) or not getattr(current_user, 'host_profile', None):
        flash('Access denied. This page is for hosts only.')
        return redirect(url_for('car.home'))

    # Option C: Check if current_user is an Admin (if this route is for admins)
    # if not isinstance(current_user, Admin):
    #     flash('Access denied. This page is for admins only.')
    #     return redirect(url_for('car.home'))
    # --- END CRITICAL FIX 2 ---

    # ... rest of route logic ...
    # Assuming you need the host object for further processing
    host = current_user.host_profile  # This should now work safely

    return render_template('some_bp/some_route.html', host=host)  # Pass host context

# ... (rest of routes/some_bp.py) ...
