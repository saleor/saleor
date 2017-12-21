from django_filters import FilterSet


class SortedFilterSet(FilterSet):
    '''
    Base class for filtersets used in dashboard views. Adds flag
    is_bound_unsorted to indicate if FilterSet has data from filters other
    than sort_by or page.
    '''
    def __init__(self, data, *args, **kwargs):
        self.is_bound_unsorted = self.set_is_bound_unsorted(data)
        super(SortedFilterSet, self).__init__(data, *args, **kwargs)

    def set_is_bound_unsorted(self, data):
        return any([key not in {'sort_by', 'page'} for key in data.keys()])
