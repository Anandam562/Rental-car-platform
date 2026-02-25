# routes/user/filters/transmission.py
from .base import BaseFilter
# from models.car import Car

class TransmissionFilter(BaseFilter):
    """Filter cars by transmission type (Manual, Automatic)."""
    param_name = 'transmission'
    VALID_TRANSMISSIONS = ['Manual', 'Automatic']

    def apply(self, query, value):
        """Apply the transmission filter."""
        if value and value in self.VALID_TRANSMISSIONS:
            from models.car import Car
            query = query.filter(Car.transmission == value)
        return query