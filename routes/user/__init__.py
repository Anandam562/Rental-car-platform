from flask import Blueprint

user_bp = Blueprint('user', __name__, url_prefix='/user')

from . import dashboard, bookings, notifications, profile, wallet

__all__ = ['user_bp', 'dashboard', 'bookings', 'profile', 'wallet', 'notifications']