import django_filters

from ...page.models import Page
from ..core.types import FilterInputObjectType
from ..utils.filters import filter_by_query_param


def filter_page_search(qs, _, value):
    page_fields = ["content", "slug", "title"]
    qs = filter_by_query_param(qs, value, page_fields)
    return qs


class PageFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method=filter_page_search)

    class Meta:
        model = Page
        fields = ["search"]


class PageFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = PageFilter
