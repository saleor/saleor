from django_filters import FilterSet


class SortedFilterSet(FilterSet):
    '''
    Base class for filtersets used in dashboard views. Adds flag
    is_bound_unsorted to indicate if FilterSet has data from filters other
    than sort_by.
    '''
    def __init__(self, data, *args, **kwargs):
        data_copy = data.copy() if data else None
        self.is_bound_unsorted = self.set_is_bound_unsorted(data_copy)
        super().__init__(data, *args, **kwargs)

    def set_is_bound_unsorted(self, data_copy):
        if data_copy and data_copy.get('sort_by', None):
            del data_copy['sort_by']
        if data_copy:
            return True
        return False
