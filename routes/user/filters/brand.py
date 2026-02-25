# routes/user/filters/brand.py
from .base import BaseFilter
# from models.car import Car

class BrandFilter(BaseFilter):
    """Filter cars by brand/make (Maruti, Hyundai, etc.)."""
    param_name = 'brand'
    # Consider defining this list dynamically from your Car data if brands vary
    VALID_BRANDS = ['Maruti', 'Hyundai', 'Tata', 'Mahindra', 'Toyota', 'Honda', 'Ford', 'Volkswagen']

    def apply(self, query, value):
        """Apply the brand filter."""
        if value and value in self.VALID_BRANDS:
            from models.car import Car
            query = query.filter(Car.make == value) # Assumes 'make' field holds brand
        return query