import django_filters
from graphene_django.filter import GlobalIDMultipleChoiceFilter

from ...shipping.models import ShippingZone
from ..channel.types import Channel
from ..core.types import FilterInputObjectType
from ..utils import resolve_global_ids_to_primary_keys
from ..utils.filters import filter_fields_containing_value


def filter_channels(qs, _, values):
    if values:
        _, channels_ids = resolve_global_ids_to_primary_keys(values, Channel)
        qs = qs.filter(channels__id__in=channels_ids)
    return qs


class ShippingZoneFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method=filter_fields_containing_value("name"))
    channels = GlobalIDMultipleChoiceFilter(method=filter_channels)

    class Meta:
        model = ShippingZone
        fields = ["search"]


class ShippingZoneFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = ShippingZoneFilter
