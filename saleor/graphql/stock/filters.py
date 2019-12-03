import django_filters
from django.db.models import Q

from ...stock.models import Stock
from ..core.types import FilterInputObjectType


def filter_product_variant(qs, _, value):
    qs = qs.filter(
        Q(product_variant__product__name__icontains=value)
        | Q(product_variant__name__icontains=value)
    )
    return qs


def filter_warehouse(qs, _, value):
    qs = qs.filter(
        Q(warehouse__name__icontains=value)
        | Q(warehouse__company_name__icontains=value)
    )
    return qs


class StockFilter(django_filters.FilterSet):
    product_variant = django_filters.CharFilter(method=filter_product_variant)
    warehouse = django_filters.CharFilter(method=filter_warehouse)

    class Meta:
        model = Stock
        fields = ["quantity", "quantity_allocated"]


class StockFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = StockFilter
