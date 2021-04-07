import django_filters
from ...store.models import Store
from ..utils.filters import filter_by_query_param, filter_range_field

def filter_store_type(qs, _, value):
    return filter_range_field(qs, "store_type", value)


def filter_search(qs, _, value):
    search_fields = ("name",)
    if value:
        qs = filter_by_query_param(qs, value, search_fields)
    return qs


class StoreFilter(django_filters.FilterSet):
    store_type =  django_filters.CharFilter(method=filter_store_type)    
    search = django_filters.CharFilter(method=filter_search)

    class Meta:
        model = Store
        fields = [
            "store_type",            
            "search",
        ]

class StoreFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = StoreFilter