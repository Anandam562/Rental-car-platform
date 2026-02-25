# routes/user/filters/base.py
from abc import ABC, abstractmethod
# from flask import request # Don't import request here

class BaseFilter(ABC):
    """Abstract base class for car listing filters."""
    param_name = None  # Must be set by subclasses

    @abstractmethod
    def apply(self, query, value):
        """Apply the filter to the SQLAlchemy query."""
        pass

    # --- CRITICAL: Ensure this method is defined correctly ---
    @classmethod
    def get_value_from_request(cls, request):
        """
        Get the filter value from the Flask request.
        This is the standard method for single-value filters.
        Override for multi-value (e.g., checkboxes) or range filters.
        """
        if cls.param_name:
            return request.args.get(cls.param_name)
        return None

    @classmethod
    def get_values_from_request(cls, request):
        """
        Get multiple filter values (e.g., for checkboxes) from the Flask request.
        Useful for filters like 'type' where multiple types can be selected.
        """
        if cls.param_name:
            return request.args.getlist(cls.param_name)
        return []
    # --- END CRITICAL ---