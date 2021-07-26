import django_filters
from graphene_django.filter import GlobalIDMultipleChoiceFilter

from ...warehouse import WarehouseClickAndCollectOption
from ...warehouse.models import Stock, Warehouse
from ..core.filters import EnumFilter
from ..core.types import FilterInputObjectType
from ..utils.filters import filter_by_query_param
from ..warehouse.enums import WarehouseClickAndCollectOptionEnum


def prefech_qs_for_filter(qs):
    return qs.prefetch_related("address")


def filter_search_warehouse(qs, _, value):
    search_fields = [
        "name",
        "address__company_name",
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


def filter_click_and_collect_option(qs, _, value):
    if value == WarehouseClickAndCollectOptionEnum.LOCAL.value:
        qs = qs.filter(
            click_and_collect_option=WarehouseClickAndCollectOption.LOCAL_STOCK
        )
    elif value == WarehouseClickAndCollectOptionEnum.ALL.value:
        qs = qs.filter(
            click_and_collect_option=WarehouseClickAndCollectOption.ALL_WAREHOUSES
        )
    elif value == WarehouseClickAndCollectOptionEnum.DISABLED.value:
        qs = qs.filter(click_and_collect_option=WarehouseClickAndCollectOption.DISABLED)
    return qs


def filter_search_stock(qs, _, value):
    search_fields = [
        "product_variant__product__name",
        "product_variant__name",
        "warehouse__name",
        "warehouse__address__company_name",
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
    is_private = django_filters.BooleanFilter(field_name="is_private")
    click_and_collect_option = EnumFilter(
        input_class=WarehouseClickAndCollectOptionEnum,
        method=filter_click_and_collect_option,
    )

    class Meta:
        model = Warehouse
        fields = ["click_and_collect_option"]


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
