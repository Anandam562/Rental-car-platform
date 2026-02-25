# routes/host/__init__.py
from flask import Blueprint

host_bp = Blueprint('host', __name__, url_prefix='/host')

# Import routes - THIS IS CRUCIAL TO REGISTER THEM
from . import dashboard, cars, auth, payments, analytics, profile, bookings, feedbacks, ratings,wallet  # Make sure 'auth' is imported