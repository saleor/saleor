from __future__ import unicode_literals

from django_filters import (CharFilter, FilterSet, OrderingFilter, RangeFilter)
from django.utils.translation import pgettext_lazy

from ...userprofile.models import User


SORT_BY_FIELDS = (
    ('email', 'email'),
    ('default_billing_address__first_name', 'name'),
    ('default_billing_address__city', 'location'),
    ('num_orders', 'num_orders'),
    ('last_order', 'last_order')
)


SORT_BY_FIELDS_LABELS = {
    'email': pgettext_lazy(
        'Customer list sorting option', 'email'),
    'default_billing_address__first_name': pgettext_lazy(
        'Customer list sorting option', 'name'),
    'default_billing_address__city': pgettext_lazy(
        'Customer list sorting option', 'location'),
    'num_orders': pgettext_lazy(
        'Customer list sorting option', 'number of orders'),
    'last_order': pgettext_lazy(
        'Customer list sorting option', 'last order')}


class CustomerFilter(FilterSet):
    sort_by = OrderingFilter(
        label=pgettext_lazy('Customer list sorting form', 'Sort by'),
        fields=SORT_BY_FIELDS,
        field_labels=SORT_BY_FIELDS_LABELS)
    email = CharFilter(
        label=pgettext_lazy('Customer list name filter', 'Email'),
        lookup_expr='icontains')
    name = CharFilter(
        label=pgettext_lazy('Customer list sorting filter', 'Name'),
        name='default_billing_address__first_name',
        lookup_expr='icontains')
    last_name = CharFilter(
        label=pgettext_lazy('Customer list sorting filter', 'Last name'),
        name='default_billing_address__last_name',
        lookup_expr='icontains')
    city = CharFilter(
        label=pgettext_lazy('Customer list sorting filter', 'City'),
        name='default_billing_address__city',
        lookup_expr='icontains')
    num_orders = RangeFilter(
        label=pgettext_lazy(
            'Customer list sorting filter', 'Number of orders'),
        name='num_orders')

    class Meta:
        model = User
        fields = ['email', 'is_active', 'is_staff']
