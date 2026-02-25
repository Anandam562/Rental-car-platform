# routes/user/filters/price_range.py
from .base import BaseFilter
# from models.car import Car

class PriceRangeFilter(BaseFilter):
    """Filter cars by price per day range."""
    # Note: This filter uses TWO parameters, so we override the base methods slightly
    param_min = 'min_price'
    param_max = 'max_price'

    def apply(self, query, value=None): # Value not used directly here
        """
        Apply the price range filter to the query.
        Gets min/max values directly from the request.
        """
        # Import request locally or pass it if needed, but here we get it from args
        from flask import request
        from models.car import Car

        min_price_str = request.args.get(self.param_min)
        max_price_str = request.args.get(self.param_max)

        try:
            if min_price_str:
                min_price = float(min_price_str)
                query = query.filter(Car.price_per_day >= min_price)
            if max_price_str:
                max_price = float(max_price_str)
                query = query.filter(Car.price_per_day <= max_price)
        except (ValueError, TypeError):
             pass # Gracefully handle invalid inputs

        return query

    # Override class methods since we use two params
    # These are not typically called by the filter manager for range filters,
    # but good to define for consistency or if needed elsewhere.
    @classmethod
    def get_value_from_request(cls, request):
        # Not directly usable for a range, but could return a tuple
        min_val = request.args.get(cls.param_min)
        max_val = request.args.get(cls.param_max)
        return (min_val, max_val) # Or just return None