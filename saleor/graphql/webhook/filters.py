import django_filters

from ..core.filters import EnumFilter
from ..core.types import FilterInputObjectType
from .enums import EventDeliveryStatusEnum, WebhookEventTypeEnum


def filter_status(qs, _, value):
    if value:
        qs = qs.filter(status=value)
    return qs


def filter_event_type(qs, _, value):
    if value:
        qs = qs.filter(event_type=value)
    return qs


class EventDeliveryFilter(django_filters.FilterSet):
    status = EnumFilter(input_class=EventDeliveryStatusEnum, method=filter_status)
    event_type = EnumFilter(input_class=WebhookEventTypeEnum, method=filter_event_type)


class EventDeliveryFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = EventDeliveryFilter
