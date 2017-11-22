from __future__ import unicode_literals

from django_filters import (CharFilter, FilterSet, OrderingFilter, RangeFilter)
from ...core.utils.filters import filter_by_customer, filter_by_location
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
    name_or_email = CharFilter(
        label=pgettext_lazy('Customer name or email filter', 'Name or email'),
        method=filter_by_customer)
    location = CharFilter(
        label=pgettext_lazy('Customer list sorting filter', 'Location'),
        method=filter_by_location)
    num_orders = RangeFilter(
        label=pgettext_lazy(
            'Customer list sorting filter', 'Number of orders'),
        name='num_orders')

    class Meta:
        model = User
        fields = ['email', 'is_active', 'is_staff']
