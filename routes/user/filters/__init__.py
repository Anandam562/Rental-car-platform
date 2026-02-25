# routes/user/filters/__init__.py
# This file makes the 'filters' directory a Python package.
# It also imports and exposes filter classes for easier access.

# --- Import filter classes ---
from .base import BaseFilter
from .car_type import CarTypeFilter
from .distance import DistanceFilter
from .transmission import TransmissionFilter
from .fuel_type import FuelTypeFilter
from .seating_capacity import SeatingCapacityFilter
# from .delivery_type import DeliveryTypeFilter # Uncomment if implemented and fixed
from .price_range import PriceRangeFilter
# from .brand import BrandFilter # Uncomment if implemented
from .model_year import ModelYearFilter
from .features import FeaturesFilter
# --- End Imports ---

# --- List of active filter classes for easy iteration ---
# Make sure this list only includes filters whose classes are correctly defined
FILTER_CLASSES = [
    CarTypeFilter,
    TransmissionFilter,
    FuelTypeFilter,
    SeatingCapacityFilter,
    # DeliveryTypeFilter, # Add only if working
    PriceRangeFilter,
    # BrandFilter, # Add only if working
    ModelYearFilter,
    FeaturesFilter,
    # DistanceFilter, # Add if you want it managed by the standard loop (though logic is special)
]
# --- End List ---

__all__ = [
    'BaseFilter',
    'CarTypeFilter',
    'TransmissionFilter',
    'FuelTypeFilter',
    'SeatingCapacityFilter',
    # 'DeliveryTypeFilter',
    'PriceRangeFilter',
    # 'BrandFilter',
    'ModelYearFilter',
    'FeaturesFilter',
    'DistanceFilter',
    'FILTER_CLASSES'
]