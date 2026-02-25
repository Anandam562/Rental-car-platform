# routes/user/filters/fuel_type.py
from .base import BaseFilter
# from models.car import Car

class FuelTypeFilter(BaseFilter):
    """Filter cars by fuel type (Petrol, Diesel, CNG, EV)."""
    param_name = 'fuel'
    VALID_FUELS = ['Petrol', 'Diesel', 'CNG', 'EV', 'Electric']

    def apply(self, query, value):
        """Apply the fuel type filter."""
        if value and value in self.VALID_FUELS:
            from models.car import Car
            normalized_value = 'EV' if value == 'Electric' else value
            query = query.filter(Car.fuel_type == normalized_value)
        return query