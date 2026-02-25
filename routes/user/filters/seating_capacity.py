# routes/user/filters/seating_capacity.py
from .base import BaseFilter
# from models.car import Car

class SeatingCapacityFilter(BaseFilter):
    """Filter cars by seating capacity range."""
    param_min = 'min_seats'
    param_max = 'max_seats'

    def apply(self, query, value=None): # Value not used directly here
        """Apply the seating capacity range filter."""
        from flask import request
        from models.car import Car

        min_seats_str = request.args.get(self.param_min)
        max_seats_str = request.args.get(self.param_max)

        try:
            if min_seats_str:
                min_seats = int(min_seats_str)
                query = query.filter(Car.seats >= min_seats)
            if max_seats_str:
                max_seats = int(max_seats_str)
                query = query.filter(Car.seats <= max_seats)
        except (ValueError, TypeError):
            pass # Gracefully handle invalid inputs
        return query

    # Override class methods if needed (similar to price range)
    @classmethod
    def get_value_from_request(cls, request):
        min_val = request.args.get(cls.param_min)
        max_val = request.args.get(cls.param_max)
        return (min_val, max_val)