from __future__ import unicode_literals

from django_filters import (
    CharFilter, ChoiceFilter, OrderingFilter, RangeFilter)
from django.utils.translation import pgettext_lazy

from ...shipping.models import COUNTRY_CODE_CHOICES, ShippingMethod
from ..filters import SortedFilterSet


SORT_BY_FIELDS = {
    'name': pgettext_lazy('Group list sorting option', 'name')}


class ShippingMethodFilter(SortedFilterSet):
    name = CharFilter(
        label=pgettext_lazy(
            'Shipping method list filter label', 'Name'),
        lookup_expr="icontains")
    price = RangeFilter(
        label=pgettext_lazy(
            'Shipping method list filter label', 'Price range'),
        name='price_per_country__price')
    country = ChoiceFilter(
        label=pgettext_lazy('Shipping method filter label', 'Country'),
        name='price_per_country__country_code',
        choices=COUNTRY_CODE_CHOICES)
    sort_by = OrderingFilter(
        label=pgettext_lazy('Product list sorting filter label', 'Sort by'),
        fields=SORT_BY_FIELDS.keys(),
        field_labels=SORT_BY_FIELDS)

    class Meta:
        model = ShippingMethod
        fields = []
