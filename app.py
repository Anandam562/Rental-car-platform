import os

from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect  # ✅

from config import Config
from models import db
# from flask_wtf.csrf import CSRFProtect
from models.admin import Admin
# Import models in an order that resolves dependencies or import them all at once
# The key is they are all imported before db.create_all()
# Importing the main classes is usually sufficient, as relationships often use strings.
from models.user import User
from routes.admin import admin_bp
from routes.api import api_bp
# Import routes
from routes.auth import auth_bp
from routes.booking import booking_bp
from routes.car import car_bp
from routes.host import host_bp  # <-- CRUCIAL: Import the host blueprint
from routes.payment import payment_bp
# --- NEW IMPORTS ---
from routes.user import user_bp  # If you have a separate user blueprint
from tasks.notifications import start_background_scheduler


# Import db first
# Import models in correct order to resolve dependencies
# Import Host before Car if Car references Host via backref (like we are doing now)
# Or ensure both are imported before relationships are configured.


# --- END NEW IMPORTS ---



def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # AFTER (Initialize CSRF with app)
    csrf = CSRFProtect(app)  # <-- Initialize CSRF protection with the app instance
    # --- END CRITICAL FIX 3 ---
    
    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)
    csrf.init_app(app)
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'  # Default login for users/hosts

    @login_manager.user_loader
    def load_user(user_id):
        """
        Load a user by ID for Flask-Login.
        Uses Session.get() as recommended in SQLAlchemy 2.0.
        """
        try:
            # --- CRITICAL FIX 4: Use Session.get() instead of Query.get() ---
            # BEFORE (Legacy - causes warning)
            # return User.query.get(int(user_id))

            # AFTER (Modern - resolves warning)
            # Try to load as User first (most common)
            user = db.session.get(User, int(user_id))  # <-- Use Session.get()
            if user and user.is_active:
                return user

            # If not found as User, try Admin
            admin = db.session.get(Admin, int(user_id))  # <-- Use Session.get()
            if admin and admin.is_active:
                return admin

            # If not found as Admin, try Host (linked to User)
            # host = db.session.get(Host, int(user_id)) # <-- Use Session.get() if Host is a UserMixin
            # if host and host.user and host.user.is_active:
            #     return host.user # Return the associated User object for Hosts
            # OR, if Host model itself inherits UserMixin:
            # host = db.session.get(Host, int(user_id)) # <-- Use Session.get()
            # if host and host.is_active:
            #     return host # Return the Host object directly

            # User/Admin/Host not found or inactive
            return None
            # --- END CRITICAL FIX 4 ---
        except (ValueError, TypeError):
            # Handle invalid user_id (e.g., not an integer)
            return None

    # --- END CRITICAL FIX 5 ---
    # ... other initializations ..

    # Create uploads directory
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(car_bp)
    app.register_blueprint(booking_bp)
    # app.register_blueprint(booking_bp, url_prefix='/booking')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(host_bp, url_prefix='/host')
    app.register_blueprint(user_bp, url_prefix='/user')
    # --- NEW REGISTRATIONS ---
    app.register_blueprint(payment_bp, url_prefix='/payment')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    # --- END NEW REGISTRATIONS ---

    # scheduler = BackgroundScheduler()
    # scheduler.add_job(func=Booking.auto_cancel_unapproved, trigger="interval", hours=1)  # Run every hour
    # scheduler.start()
    # app.register_blueprint(host_bp, url_prefix='/host')  # <-- CRUCIAL: Register the host blueprint

    return app


app = create_app()

# Create tables
with app.app_context():
    # db.session.execute(db.text('SET FOREIGN_KEY_CHECKS=0;'))
    # db.drop_all()
    # db.session.execute(db.text('SET FOREIGN_KEY_CHECKS=1;'))
    start_background_scheduler()
    db.create_all()
    # --- CRITICAL FIX 8: Create Default Admin ---
    from models.admin import create_default_admin

    create_default_admin()
    # --- END CRITICAL FIX 8 ---

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)