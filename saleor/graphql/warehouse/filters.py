import django_filters

from ...warehouse.models import Warehouse
from ..core.types import FilterInputObjectType
from ..utils import filter_by_query_param


def prefech_qs_for_filter(qs):
    return qs.select_related("address")


def filter_search(qs, _, value):
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
    qs = prefech_qs_for_filter(qs)

    if value:
        qs = filter_by_query_param(qs, value, search_fields)
    return qs


class WarehouseFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method=filter_search)

    class Meta:
        model = Warehouse
        fields = []


class WarehouseFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = WarehouseFilter
