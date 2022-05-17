import django_filters
from saleor.graphql.core.types import FilterInputObjectType
from graphene_django.filter import GlobalIDMultipleChoiceFilter
from custom import models
from saleor.graphql.utils.filters import filter_by_query_param


def filter_search_custom(qs, _, value):
    search_fields = [
        "name",
        "email",
        "description",
    ]

    if value:
        qs = filter_by_query_param(qs, value, search_fields)
    return qs


class CustomFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method=filter_search_custom)
    ids = GlobalIDMultipleChoiceFilter(field_name="id")

    class Meta:
        model = models.Custom
        fields = []


class CustomFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = CustomFilter
