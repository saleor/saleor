import django_filters

from ...menu.models import Menu
from ..core.types import FilterInputObjectType
from ..utils import filter_by_query_param


def filter_menu_search(qs, _, value):
    plugin_fields = ["name"]
    qs = filter_by_query_param(qs, value, plugin_fields)
    return qs


class MenuFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method=filter_menu_search)

    class Meta:
        model = Menu
        fields = ["search"]


class MenuFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = MenuFilter
