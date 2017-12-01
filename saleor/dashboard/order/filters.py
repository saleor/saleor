from __future__ import unicode_literals

from django_filters import (
    CharFilter, ChoiceFilter, DateFromToRangeFilter, NumberFilter, RangeFilter,
    OrderingFilter)
from django import forms
from django.utils.translation import pgettext_lazy
from payments import PaymentStatus

from ...core.utils.filters import filter_by_order_customer
from ...order.models import Order
from ...order import OrderStatus
from ..filters import SortedFilterSet
from ..widgets import DateRangeWidget, PriceRangeWidget


SORT_BY_FIELDS = (
    ('pk', 'pk'),
    ('status', 'status'),
    ('payments__status', 'payment_status'),
    ('user__email', 'email'),
    ('created', 'created'),
    ('total_net', 'total')
)

SORT_BY_FIELDS_LABELS = {
    'pk': pgettext_lazy('Order list sorting option', '#'),
    'status': pgettext_lazy('Order list sorting option', 'status'),
    'payments__status': pgettext_lazy('Order list sorting option', 'payment'),
    'user__email': pgettext_lazy('Order list sorting option', 'email'),
    'created': pgettext_lazy('Order list sorting option', 'created'),
    'total_net': pgettext_lazy('Order list sorting option', 'created')}


class OrderFilter(SortedFilterSet):
    id = NumberFilter(
        label=pgettext_lazy('Order list filter label', 'ID'))
    name_or_email = CharFilter(
        label=pgettext_lazy(
            'Order list filter label', 'Customer name or email'),
        method=filter_by_order_customer)
    created = DateFromToRangeFilter(
        label=pgettext_lazy('Order list filter label', 'Placed on'),
        name='created', widget=DateRangeWidget)
    status = ChoiceFilter(
        label=pgettext_lazy(
            'Order list filter label', 'Order status'),
        choices=OrderStatus.CHOICES,
        empty_label=pgettext_lazy('Filter empty choice label', 'All'),
        widget=forms.Select)
    payment_status = ChoiceFilter(
        label=pgettext_lazy('Order list filter label', 'Payment status'),
        name='payments__status',
        choices=PaymentStatus.CHOICES,
        empty_label=pgettext_lazy('Filter empty choice label', 'All'),
        widget=forms.Select)
    total_net = RangeFilter(
        label=pgettext_lazy('Order list filter label', 'Total'),
        widget=PriceRangeWidget)
    sort_by = OrderingFilter(
        label=pgettext_lazy('Order list filter label', 'Sort by'),
        fields=SORT_BY_FIELDS,
        field_labels=SORT_BY_FIELDS_LABELS)

    class Meta:
        model = Order
        fields = []
