# routes/user/filters/model_year.py
from .base import BaseFilter
# from models.car import Car

class ModelYearFilter(BaseFilter):
    """
    Filter cars by minimum model year.
    Expects URL parameter like `min_year=2020`.
    """
    param_name = 'min_year'
    MIN_VALID_YEAR = 1950
    MAX_VALID_YEAR = 2030

    def apply(self, query, value):
        """Apply the model year filter to the query."""
        # value comes from get_value_from_request (single value)
        if not value:
            return query

        try:
            min_year = int(value)
            if min_year < self.MIN_VALID_YEAR or min_year > self.MAX_VALID_YEAR:
                 return query

            from models.car import Car
            query = query.filter(Car.year >= min_year)

        except (ValueError, TypeError):
            pass
        return query