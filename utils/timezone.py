# utils/timezone.py
import pytz
from datetime import datetime

# Define commonly used timezones
UTC_TZ = pytz.utc
IST_TZ = pytz.timezone('Asia/Kolkata')

def utc_to_ist(utc_dt):
    """
    Convert a UTC datetime object to IST.
    Args:
        utc_dt (datetime): A timezone-aware datetime object in UTC.
    Returns:
        datetime: A timezone-aware datetime object in IST.
    """
    if utc_dt.tzinfo is None:
        # If naive, assume it's UTC
        utc_dt = UTC_TZ.localize(utc_dt)
    return utc_dt.astimezone(IST_TZ)

def ist_to_utc(ist_dt):
    """
    Convert an IST datetime object to UTC.
    Args:
        ist_dt (datetime): A timezone-aware datetime object in IST.
    Returns:
        datetime: A timezone-aware datetime object in UTC.
    """
    if ist_dt.tzinfo is None:
        # If naive, assume it's IST
        ist_dt = IST_TZ.localize(ist_dt)
    return ist_dt.astimezone(UTC_TZ)

def get_current_ist_time():
    """
    Get the current time in IST.
    Returns:
        datetime: A timezone-aware datetime object representing the current time in IST.
    """
    utc_now = datetime.utcnow()
    utc_now_with_tz = UTC_TZ.localize(utc_now)
    return utc_to_ist(utc_now_with_tz)

# --- CRITICAL FIX: Helper to convert DB UTC datetime to IST ---
def db_utc_to_ist(db_utc_dt):
    """
    Safely convert a datetime object retrieved from the database (assumed UTC)
    to IST. Handles naive datetimes.
    Args:
        db_utc_dt (datetime): A datetime object from the database (treated as UTC).
    Returns:
        datetime: A timezone-aware datetime object in IST.
    """
    if db_utc_dt.tzinfo is None:
        # If naive datetime from DB, localize it as UTC first
        db_utc_dt = UTC_TZ.localize(db_utc_dt)
    # Now convert the UTC datetime to IST
    return utc_to_ist(db_utc_dt)
# --- END CRITICAL FIX ---

