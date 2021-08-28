import django_filters
from graphene_django.filter import GlobalIDMultipleChoiceFilter

from saleor.graphql.core.types import FilterInputObjectType
from saleor.graphql.utils.filters import filter_by_query_param
from saleor.stock_transfer import models


def filter_search_stock_transfer(qs, _, value):
    search_fields = [
        "request_name",
        "is_active"
    ]

    if value:
        qs = filter_by_query_param(qs, value, search_fields)
    return qs


class StockTransferFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method=filter_search_stock_transfer)
    ids = GlobalIDMultipleChoiceFilter(field_name="id")

    class Meta:
        model = models.StockTransfer
        fields = []


class StockTransferFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = StockTransferFilter
