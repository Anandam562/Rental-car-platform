# routes/admin/dashboard.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from . import admin_bp
from models import db
from models.user import User
from models.host import Host
from models.car import Car
from models.booking import Booking
from models.admin import Admin  # <-- Import Admin model


@admin_bp.route('/')  # <-- This creates the 'admin.dashboard' endpoint
@login_required
def dashboard():
    """
    Admin dashboard overview.
    This is the 'admin.dashboard' endpoint.
    """
    # --- CRITICAL FIX 1: Authorization check (ensure user is an admin) ---
    # BEFORE (Incorrect - Might have checked for host_profile or user attributes)
    # if not hasattr(current_user, 'host_profile') or not current_user.host_profile:
    #     flash('Access denied.')
    #     return redirect(url_for('car.home'))

    # AFTER (Correct - Check if current_user is an Admin instance)
    if not isinstance(current_user, Admin):  # <-- Check user type
        flash('Access denied.')
        return redirect(url_for('car.home'))
    # --- END CRITICAL FIX 1 ---

    # --- Get statistics ---
    total_users = User.query.count()
    total_hosts = Host.query.count()
    total_cars = Car.query.count()
    total_bookings = Booking.query.count()
    total_admins = Admin.query.count()

    # Get recent entities
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_hosts = Host.query.order_by(Host.created_at.desc()).limit(5).all()
    recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(5).all()
    recent_cars = Car.query.order_by(Car.created_at.desc()).limit(5).all()
    recent_admins = Admin.query.order_by(Admin.created_at.desc()).limit(5).all()
    # --- End Get Statistics ---

    return render_template('admin/dashboard.html',
                           total_users=total_users,
                           total_hosts=total_hosts,
                           total_cars=total_cars,
                           total_bookings=total_bookings,
                           total_admins=total_admins,
                           recent_users=recent_users,
                           recent_hosts=recent_hosts,
                           recent_bookings=recent_bookings,
                           recent_cars=recent_cars,
                           recent_admins=recent_admins)
