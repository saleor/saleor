import django_filters

from ..core.types import FilterInputObjectType


def filter_gift_card_tag(qs, _, value):
    if not value:
        return qs
    return qs.filter(tag__ilike=value)


class GiftCardFilter(django_filters.FilterSet):
    tag = django_filters.CharFilter(method=filter_gift_card_tag)


class GiftCardFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = GiftCardFilter
