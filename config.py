import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-super-secret-key-change-this-in-production-12345')
    # --- CRITICAL FIX 2: Enable CSRF Protection ---
    WTF_CSRF_ENABLED = True  # Enable CSRF protection globally
    WTF_CSRF_TIME_LIMIT = 3600  # Optional: Set CSRF token expiration (1 hour)
    WTF_CSRF_SSL_STRICT = False  # Optional: Set to True if using HTTPS
    # --- END CRITICAL FIX 2 ---


    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'mysql+pymysql://root:root@localhost/cars_db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False


    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

    # Razorpay configuration
    RAZORPAY_KEY_ID = os.getenv('RAZORPAY_KEY_ID')
    RAZORPAY_KEY_SECRET = os.getenv('RAZORPAY_KEY_SECRET')