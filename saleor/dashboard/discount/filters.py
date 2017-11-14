from __future__ import unicode_literals

from django_filters import (FilterSet, RangeFilter, OrderingFilter)
from django.utils.translation import pgettext_lazy
from django_prices.models import PriceField

from ...discount.models import Sale


SORT_BY_FIELDS = {
    'name': pgettext_lazy('Product list sorting option', 'name'),
    'discount': pgettext_lazy('Product list sorting option', 'discount')}


class SaleFilter(FilterSet):
    sort_by = OrderingFilter(
        label=pgettext_lazy('Product list sorting form', 'Sort by'),
        fields=SORT_BY_FIELDS.keys(),
        field_labels=SORT_BY_FIELDS
    )

    class Meta:
        model = Sale
        fields = ['categories', 'type', 'value']
        filter_overrides = {
            PriceField: {
                'filter_class': RangeFilter
            }
        }
