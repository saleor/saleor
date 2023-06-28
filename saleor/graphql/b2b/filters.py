import django_filters
from django.db.models import Q
from ...discount import DiscountValueType
from ...b2b.models import CustomerGroup, CategoryDiscount
from ..utils import resolve_global_ids_to_primary_keys
from ..core.filters import ListObjectTypeFilter, GlobalIDMultipleChoiceFilter
from ..channel.types import Channel


def filter_channels(qs, _, values):
    if values:
        _, channels_ids = resolve_global_ids_to_primary_keys(values, Channel)
        qs = qs.filter(channel_id__in=channels_ids).distinct()
    return qs



def filter_discount_type(qs, _, values):
    if values:
        query = Q()
        if DiscountValueType.FIXED in values:
            query |= Q(
                value_type=DiscountValueType.FIXED.value #type: ignore
            )
        if DiscountValueType.PERCENTAGE in values:
            query |= Q(
                value_type=DiscountValueType.PERCENTAGE.value #type: ignore
            )
        qs = qs.filter(query)
    return qs
    

def filter_serach(qs, _, value):
    if value:
        qs = qs.filter(name__trigram_similar=value)
    return qs


class CustomerGroupFilters(django_filters.FilterSet):
    search = django_filters.CharFilter(method=filter_serach)
    channels = GlobalIDMultipleChoiceFilter(method=filter_channels)

    class Meta:
        model = CustomerGroup


class CategoryDiscountFilter(django_filters.FilterSet):
    discount_type = ListObjectTypeFilter(
        input_class=DiscountValueType, method=filter_discount_type
    )

    class Meta:
        model = CategoryDiscount
