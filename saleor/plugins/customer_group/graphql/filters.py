import django_filters

from saleor.graphql.core.filters import MetadataFilterBase
from saleor.graphql.core.types.filter_input import FilterInputObjectType
from saleor.graphql.utils.filters import filter_by_query_param

from .. import models


def filter_group_search(qs, _, value):
    group_fields = ["name"]
    qs = filter_by_query_param(qs, value, group_fields)
    return qs


class GroupFilter(MetadataFilterBase):
    search = django_filters.CharFilter(method=filter_group_search)

    class Meta:
        model = models.CustomerGroup
        fields = ["search"]


class GroupFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = GroupFilter
