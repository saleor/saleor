from __future__ import unicode_literals
from django_filters import FilterSet


class SortedFilterSet(FilterSet):
    '''
    Base class for filtersets used in dashboard views. Adds flag
    is_bound_unsorted to indicate if FilterSet has data from filters other
    than sort_by.
    '''
    def __init__(self, data, *args, **kwargs):
        data_copy = data.copy() if data else None
        print data
        if data:
            if data_copy.get('sort_by', None):
                del data_copy['sort_by']
            if data_copy:
                self.is_bound_unsorted = True
        else:
            self.is_bound_unsorted = False
        super(SortedFilterSet, self).__init__(data, *args, **kwargs)
