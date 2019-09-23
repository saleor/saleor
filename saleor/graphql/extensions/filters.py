import django_filters

from ...extensions.models import PluginConfiguration
from ..core.types import FilterInputObjectType
from ..utils import filter_by_query_param


def filter_plugin_search(qs, _, value):
    plugin_fields = ["name", "description"]
    qs = filter_by_query_param(qs, value, plugin_fields)
    return qs


class PluginFilter(django_filters.FilterSet):
    active = django_filters.BooleanFilter()
    search = django_filters.CharFilter(method=filter_plugin_search)

    class Meta:
        model = PluginConfiguration
        fields = ["active", "search"]


class PluginFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = PluginFilter
