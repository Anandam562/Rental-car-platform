# routes/user/filters/some_filter.py
from routes.user.filters import BaseFilter


class SomeFilter(BaseFilter):
    param_name = 'something'

    # --- WRONG: Incorrect signature for a classmethod ---
    @classmethod
    def get_value_from_request(self, request): # <-- Should be 'cls', not 'self'
        if self.param_name: # <-- Should be 'cls.param_name'
            return request.args.get(self.param_name) # <-- Should be 'cls.param_name'
        return None
    # --- END WRONG ---