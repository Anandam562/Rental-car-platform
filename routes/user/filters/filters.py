# routes/user/filters/filters.py
# Central place to manage active filters
# from flask import request # Import inside functions if needed directly
# from . import FILTER_CLASSES # Import the list
from routes.user.filters import FeaturesFilter


def apply_filters_to_query(query, flask_request):
    """
    Iterates through active filters and applies them to the SQLAlchemy query.
    Handles standard single-value, multi-value (like checkboxes), and range filters.
    """
    # Import here to avoid potential circular import issues at init time
    from . import FILTER_CLASSES

    for FilterClass in FILTER_CLASSES:
        # --- CRITICAL: This is the line that was failing ---
        # Ensure FilterClass.get_value_from_request is correctly defined with @classmethod
        # --- END CRITICAL ---

        # Determine how to get the value based on filter type or convention
        # Option 1: Check for specific method names indicating multi-value
        # if hasattr(FilterClass, 'get_values_from_request'):
        #     values = FilterClass.get_values_from_request(flask_request)
        #     if values: # Apply if list is not empty
        #         filter_instance = FilterClass()
        #         query = filter_instance.apply(query, values)
        # else:
        #     # Standard single value
        #     value = FilterClass.get_value_from_request(flask_request)
        #     if value:
        #         filter_instance = FilterClass()
        #         query = filter_instance.apply(query, value)

        # Option 2: Let the filter class decide internally (often better)
        # The filter's apply method can call request.args.get or getlist as needed
        # But we still need to get the value(s) to decide if we should instantiate and apply

        # --- BEST PRACTICE: Let the filter handle its value retrieval internally ---
        # Instantiate the filter
        filter_instance = FilterClass()

        # Let the filter's apply method get its own values from the request if needed
        # This requires modifying the apply methods slightly or passing the request.
        # However, the standard pattern is to get the value here and pass it in.
        # Let's stick to the pattern: get value, check if exists, apply.

        # --- HANDLE DIFFERENT FILTER TYPES ---
        # Check if it's a range filter (has min/max params)
        if hasattr(FilterClass, 'param_min') or hasattr(FilterClass, 'param_max'):
            # For range filters, the apply method handles getting its own values from request
            # Pass None or a dummy value, or just call apply directly
            # The filter's apply method signature should match: apply(self, query, value=None)
            query = filter_instance.apply(query)
        # Check if it's a multi-value filter (like FeaturesFilter)
        elif FilterClass == FeaturesFilter: # Specific handling for known multi-value filter
             values = FilterClass.get_value_from_request(flask_request) # Gets list
             if values: # Apply if list is not empty
                 query = filter_instance.apply(query, values)
        else:
            # Standard single value filter
            value = FilterClass.get_value_from_request(flask_request)
            if value: # Apply if value exists (handles empty strings, None)
                # Pass the value to the instance's apply method
                query = filter_instance.apply(query, value)
        # --- END HANDLING ---

    return query