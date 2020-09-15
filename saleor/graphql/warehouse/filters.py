import django_filters
from graphene_django.filter import GlobalIDMultipleChoiceFilter

from ...warehouse.models import Stock, Warehouse
from ..core.types import FilterInputObjectType
from ..utils.filters import filter_by_query_param


def prefech_qs_for_filter(qs):
    return qs.prefetch_related("address")


def filter_search_warehouse(qs, _, value):
    search_fields = [
        "name",
        "company_name",
        "email",
        "address__street_address_1",
        "address__street_address_2",
        "address__city",
        "address__postal_code",
        "address__phone",
    ]

    if value:
        qs = prefech_qs_for_filter(qs)
        qs = filter_by_query_param(qs, value, search_fields)
    return qs


def filter_search_stock(qs, _, value):
    search_fields = [
        "product_variant__product__name",
        "product_variant__name",
        "warehouse__name",
        "warehouse__company_name",
    ]
    if value:
        qs = qs.select_related("product_variant", "warehouse").prefetch_related(
            "product_variant__product"
        )
        qs = filter_by_query_param(qs, value, search_fields)
    return qs


class WarehouseFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method=filter_search_warehouse)
    ids = GlobalIDMultipleChoiceFilter(field_name="id")

    class Meta:
        model = Warehouse
        fields = []


class WarehouseFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = WarehouseFilter


class StockFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method=filter_search_stock)

    class Meta:
        model = Stock
        fields = ["quantity"]


class StockFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = StockFilter
