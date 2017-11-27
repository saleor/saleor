from __future__ import unicode_literals

from django_filters import (
    CharFilter, ChoiceFilter, DateFromToRangeFilter, FilterSet, RangeFilter,
    OrderingFilter)
from django import forms
from django.utils.translation import pgettext_lazy
from django_prices.models import PriceField
from payments import PaymentStatus

from ...core.utils.filters import filter_by_customer
from ...order.models import Order
from ...order import OrderStatus
from ..widgets import DateRangeWidget


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


class OrderFilter(FilterSet):
    status = ChoiceFilter(
        label=pgettext_lazy(
            'Order list is published filter label', 'Order status'),
        choices=OrderStatus.CHOICES,
        empty_label=pgettext_lazy('Filter empty choice label', 'All'),
        widget=forms.Select)
    payment_status = ChoiceFilter(
        label=pgettext_lazy(
            'Order list sorting filter label', 'Payment status'),
        name='payments__status',
        choices=PaymentStatus.CHOICES,
        empty_label=pgettext_lazy('Filter empty choice label', 'All'),
        widget=forms.Select)
    name_or_email = CharFilter(
        label=pgettext_lazy(
            'Customer name or email filter label', 'Customer name or email'),
        method=filter_by_customer)
    sort_by = OrderingFilter(
        label=pgettext_lazy('Order list sorting filter label', 'Sort by'),
        fields=SORT_BY_FIELDS,
        field_labels=SORT_BY_FIELDS_LABELS)
    created = DateFromToRangeFilter(
        label=pgettext_lazy('Order list sorting filter label', 'Placed on'),
        name='created', widget=DateRangeWidget)

    class Meta:
        model = Order
        fields = ['id', 'total_net']
        filter_overrides = {
            PriceField: {
                'filter_class': RangeFilter
            }
        }
