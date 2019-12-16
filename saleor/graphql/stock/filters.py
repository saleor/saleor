import django_filters

from ...stock.models import Stock
from ..core.types import FilterInputObjectType
from ..utils import filter_by_query_param


def filter_search(qs, _, value):
    search_fields = [
        "product_variant__product__name",
        "product_variant__name",
        "warehouse__name",
        "warehouse__company_name",
    ]
    qs = qs.select_related("product_variant", "warehouse").prefetch_related(
        "product_variant__product"
    )
    if value:
        qs = filter_by_query_param(qs, value, search_fields)
    return qs


class StockFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method=filter_search)

    class Meta:
        model = Stock
        fields = ["quantity", "quantity_allocated"]


class StockFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = StockFilter
