import django_filters

from ...shipping.models import ShippingZone
from ..core.types import FilterInputObjectType
from ..utils.filters import filter_fields_containing_value


class ShippingZoneFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method=filter_fields_containing_value("name"))

    class Meta:
        model = ShippingZone
        fields = ["search"]


class ShippingZoneFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = ShippingZoneFilter
