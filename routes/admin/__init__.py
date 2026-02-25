# routes/admin/__init__.py
from flask import Blueprint

# Create the admin blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Import route modules to register them with the blueprint
from . import auth, dashboard, users, hosts, cars, bookings, transactions, admins

__all__ = ['admin_bp', 'auth', 'dashboard', 'users', 'hosts', 'cars', 'bookings', 'transactions', 'admins']