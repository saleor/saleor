import django_filters

from ...shipping.models import ShippingZone
from ..channel.types import Channel
from ..core.doc_category import DOC_CATEGORY_SHIPPING
from ..core.filters import GlobalIDMultipleChoiceFilter
from ..core.types import FilterInputObjectType
from ..utils import resolve_global_ids_to_primary_keys


def filter_channels(qs, _, values):
    if values:
        _, channels_ids = resolve_global_ids_to_primary_keys(values, Channel)
        qs = qs.filter(channels__id__in=channels_ids)
    return qs


def filter_shipping_zones_search(qs, _, value):
    return qs.filter(name__ilike=value)


class ShippingZoneFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method=filter_shipping_zones_search)
    channels = GlobalIDMultipleChoiceFilter(method=filter_channels)

    class Meta:
        model = ShippingZone
        fields = ["search"]


class ShippingZoneFilterInput(FilterInputObjectType):
    class Meta:
        doc_category = DOC_CATEGORY_SHIPPING
        filterset_class = ShippingZoneFilter
