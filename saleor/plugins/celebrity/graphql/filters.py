import django_filters

from saleor.graphql.core.filters import MetadataFilterBase
from saleor.graphql.core.types.filter_input import FilterInputObjectType
from saleor.graphql.utils.filters import filter_by_query_param

from .. import models


def filter_celebrity_search(qs, _, value):
    celebrity_fields = ["first_name", "phone_number", "email"]
    qs = filter_by_query_param(qs, value, celebrity_fields)
    return qs


class CelebrityFilter(MetadataFilterBase):
    search = django_filters.CharFilter(method=filter_celebrity_search)

    class Meta:
        model = models.Celebrity
        fields = ["search"]


class CelebrityFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = CelebrityFilter
