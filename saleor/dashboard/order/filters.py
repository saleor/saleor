from __future__ import unicode_literals

from django_filters import (ChoiceFilter, FilterSet, RangeFilter, OrderingFilter)
from django.utils.translation import pgettext_lazy
from django_prices.models import PriceField
from payments import PaymentStatus

from ...order.models import Order


SORT_BY_FIELDS = {
    'pk': pgettext_lazy('Order list sorting option', '#'),
    'status': pgettext_lazy('Order list sorting option', 'status'),
    'payments__status': pgettext_lazy('Order list sorting option', 'payment'),
    'user__email': pgettext_lazy('Order list sorting option', 'email'),
    'created': pgettext_lazy('Order list sorting option', 'created'),
    'total_net': pgettext_lazy('Order list sorting option', 'created')}


class OrderFilter(FilterSet):
    sort_by = OrderingFilter(
        label=pgettext_lazy('Order list sorting filter', 'Sort by'),
        fields=SORT_BY_FIELDS.keys(),
        field_labels=SORT_BY_FIELDS)
    payment_status = ChoiceFilter(
        label=pgettext_lazy('Order list sorting filter', 'Payment status'),
        name='payments__status', choices=PaymentStatus.CHOICES)

    class Meta:
        model = Order
        fields = ['status', 'created', 'user_email', 'total_net']
        filter_overrides = {
            PriceField: {
                'filter_class': RangeFilter
            }
        }
