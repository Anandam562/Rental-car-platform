# routes/user/filters/distance.py
from .base import BaseFilter
# from models.car import Car

class DistanceFilter(BaseFilter):
    """
    Filter cars by maximum distance from the user's location.
    This filter works differently: it operates on a list of cars
    AFTER the main database query and distance calculation/sorting.
    Expects URL parameter like `max_distance=50`.
    """
    param_name = 'max_distance'

    def apply(self, query, value):
        """
        This filter's main logic is applied AFTER the initial query
        and distance calculation in the route (routes/car.py).
        This method on the query itself is a placeholder.
        The actual filtering happens in the route or via the static method below.
        """
        # Distance filtering is handled in routes/car.py after sorting.
        # Returning the query unchanged signals it's processed elsewhere.
        # This class mainly defines the parameter name.
        return query

    @staticmethod
    def filter_car_list(cars, max_distance_km):
        """
        Static method to filter a list of Car objects by a maximum distance.
        Assumes each car in the list has a 'display_distance_km' attribute
        calculated beforehand (e.g., in routes/car.py).

        Args:
            cars (list): List of Car objects, potentially with 'display_distance_km'.
            max_distance_km (str or float): Maximum allowed distance in kilometers.

        Returns:
            list: Filtered list of Car objects within the max distance.
        """
        if max_distance_km in [None, '', '']:
            return cars # No distance filter applied

        try:
            max_dist = float(max_distance_km)
        except (ValueError, TypeError):
            return cars # Invalid max distance, return all

        # Filter the list based on the pre-calculated distance attribute
        return [car for car in cars if hasattr(car, 'display_distance_km') and car.display_distance_km <= max_dist]

    # Override class method to get the distance value
    @classmethod
    def get_value_from_request(cls, request):
        return request.args.get(cls.param_name)