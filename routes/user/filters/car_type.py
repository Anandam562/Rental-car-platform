# routes/user/filters/car_type.py
from .base import BaseFilter
# from models.car import Car

class CarTypeFilter(BaseFilter):
    """Filter cars by type (SUV, Hatchback, Sedan, etc.)."""
    param_name = 'type'
    VALID_TYPES = ['SUV', 'Hatchback', 'Sedan', 'MUV', 'Luxury', 'EV']

    def apply(self, query, value):
        """Apply the car type filter."""
        # Example: Filter by a 'car_type' field on Car model
        # Adjust 'car_type' to your actual field name
        if value and value in self.VALID_TYPES:
             from models.car import Car
             query = query.filter(Car.car_type == value)
        return query

    # --- CRITICAL: Ensure this method is defined correctly ---
    # Inherit the default get_value_from_request from BaseFilter
    # Or override if needed, but ALWAYS use @classmethod
    # @classmethod
    # def get_value_from_request(cls, request):
    #     # Use getlist if multiple values are expected (e.g., checkboxes)
    #     # return request.args.getlist(cls.param_name)
    #     # Or use get for single value
    #     return super().get_value_from_request(request) # Uses BaseFilter's logic
    # --- END CRITICAL ---