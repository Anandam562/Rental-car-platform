# routes/user/filters/delivery_type.py
from .base import BaseFilter
# from models.car import Car # Import when needed inside apply method

class DeliveryTypeFilter(BaseFilter):
    """
    Filter cars by delivery type (Self Pickup, Home Delivery, Airport Delivery).
    Expects URL parameter like `delivery=Self Pickup`.
    Note: This assumes your Car model has a way to indicate delivery options.
    This could be boolean flags (e.g., has_home_delivery), a string field (delivery_type),
    or derived from location/host details.
    For now, let's assume a simple string field `delivery_type` exists on Car.
    """
    param_name = 'delivery'
    VALID_DELIVERY_TYPES = {'Self Pickup', 'Home Delivery', 'Airport Delivery'}

    def apply(self, query, value):
        """
        Apply the delivery type filter to the query.
        """
        # Example implementation - adjust based on your actual Car model fields/logic
        if value and value in self.VALID_DELIVERY_TYPES:
            # This is a placeholder. You need to implement logic based on how
            # delivery type is represented/stored in your Car model.
            # Option 1: If Car has a 'delivery_type' field:
            # from models.car import Car
            # query = query.filter(Car.delivery_type == value)

            # Option 2: If delivery type is derived (e.g., based on location or host setting)
            # You would need more complex logic here, possibly involving joins or subqueries.
            # For example, if 'Self Pickup' means car.location is used:
            # if value == 'Self Pickup':
            #     # Logic already handled by location search? Or flag cars as self-pickup?

            # For demonstration, let's assume Option 1 with a 'delivery_option' field
            from models.car import Car
            # Normalize value if needed (e.g., handle case variations)
            normalized_value = value.strip().title() # Capitalize words
            query = query.filter(Car.delivery_option == normalized_value) # Adjust field name

        return query
