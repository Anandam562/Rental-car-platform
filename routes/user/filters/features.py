# routes/user/filters/features.py
from .base import BaseFilter
# from models.car import Car

class FeaturesFilter(BaseFilter):
    """
    Filter cars by specific features (e.g., AC, Bluetooth, Sunroof, GPS).
    Expects URL parameters like `features=AC&features=GPS`.
    Assumes Car model has boolean fields like has_ac, has_bluetooth, etc.
    """
    param_name = 'features' # Use get_values_from_request for multiple values
    VALID_FEATURES = {'ac', 'bluetooth', 'sunroof', 'gps', 'usb_port', 'reverse_camera'}

    def apply(self, query, values): # 'values' is a list from get_values_from_request
        """
        Apply the features filter to the query.
        Filters cars that have ALL the selected features enabled.
        """
        # values comes from get_values_from_request (list)
        if not values:
            return query

        # Sanitize and normalize feature names
        selected_features = [f.lower().strip() for f in values if f.lower().strip() in self.VALID_FEATURES]

        if not selected_features:
            return query

        from models.car import Car

        # Apply filter for each selected feature (AND logic)
        filter_conditions = []
        for feature in selected_features:
            # Map feature name to Car model field (assumes naming convention)
            field_name = f"has_{feature}"
            if hasattr(Car, field_name):
                filter_conditions.append(getattr(Car, field_name) == True)

        if filter_conditions:
            # Use * to unpack the list of conditions
            query = query.filter(*filter_conditions)

        return query

    # Override to get multiple values correctly
    @classmethod
    def get_value_from_request(cls, request):
        """
        Override to get a LIST of values for multi-select filters.
        """
        # Use getlist to get all values for the 'features' parameter
        return request.args.getlist(cls.param_name) # Returns a list, even if empty or one item