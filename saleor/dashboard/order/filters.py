from __future__ import unicode_literals

from django_filters import (FilterSet, RangeFilter, OrderingFilter)
from django.utils.translation import pgettext_lazy
from django_prices.models import PriceField

from ...order.models import Order


SORT_BY_FIELDS = {
    'status': pgettext_lazy('Sale list sorting option', 'status'),
    'created': pgettext_lazy('Sale list sorting option', 'created'),
    'user_email': pgettext_lazy('Sale list sorting option', 'user_email')}


class OrderFilter(FilterSet):
    sort_by = OrderingFilter(
        label=pgettext_lazy('Sale list sorting form', 'Sort by'),
        fields=SORT_BY_FIELDS.keys(),
        field_labels=SORT_BY_FIELDS
    )

    class Meta:
        model = Order
        fields = ['status', 'created', 'user_email', 'total_net']
        filter_overrides = {
            PriceField: {
                'filter_class': RangeFilter
            }
        }
