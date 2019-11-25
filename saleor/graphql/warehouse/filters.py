import django_filters
from django.db.models import Q

from ...warehouse.models import Warehouse
from ..core.types import FilterInputObjectType


def filter_string(qs, name, value):
    lookup = "__".join([name, "icontains"])
    return qs.filter(**{lookup: value})


def filter_address(qs, _, value):
    qs = qs.filter(
        Q(address__street_address_1__icontains=value)
        | Q(address__street_address_2__icontains=value)
        | Q(address__city__icontains=value)
        | Q(address__postal_code=value)
        | Q(address__phone__contains=value)
    )
    return qs


class WarehouseFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(method=filter_string)
    company_name = django_filters.CharFilter(method=filter_string)
    email = django_filters.CharFilter(method=filter_string)
    address = django_filters.CharFilter(method=filter_address)

    class Meta:
        model = Warehouse
        fields = []


class WarehouseFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = WarehouseFilter
