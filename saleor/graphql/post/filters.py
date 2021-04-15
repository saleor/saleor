import django_filters
from ..utils.filters import filter_by_query_param, filter_range_field
from ..core.types import FilterInputObjectType
from ...post import models

def filter_store(qs, _, value):
    return filter_range_field(qs, "store", value)


def filter_search(qs, _, value):
    search_fields = ("title",)
    if value:
        qs = filter_by_query_param(qs, value, search_fields)
    return qs


class PostFilter(django_filters.FilterSet):
    store =  django_filters.CharFilter(method=filter_store) 
    search = django_filters.CharFilter(method=filter_search)

    class Meta:
        model = models.Post
        fields = [
            "store",
            "search",
        ]

class PostFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = PostFilter