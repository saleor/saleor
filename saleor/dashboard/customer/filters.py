from __future__ import unicode_literals

from django_filters import (
    CharFilter, ChoiceFilter, FilterSet, OrderingFilter, RangeFilter)
from ...core.utils.filters import filter_by_customer, filter_by_location
from django.utils.translation import pgettext_lazy
from django import forms

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

IS_ACTIVE_CHOICES = (
    ('1', pgettext_lazy('Is active filter choice', 'Active')),
    ('0', pgettext_lazy('Is active filter choice', 'Not active')))

IS_STAFF_CHOICES = (
    ('1', pgettext_lazy('Is active filter choice', 'Is staff')),
    ('0', pgettext_lazy('Is active filter choice', 'Is not staff')))


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
    is_active = ChoiceFilter(
        label=pgettext_lazy(
            'Customer list is published filter label', 'Is active'),
        choices=IS_ACTIVE_CHOICES,
        empty_label=pgettext_lazy('Filter empty choice label', 'All'),
        widget=forms.Select)
    is_staff = ChoiceFilter(
        label=pgettext_lazy(
            'Customer list is published filter label', 'Is staff'),
        choices=IS_STAFF_CHOICES,
        empty_label=pgettext_lazy('Filter empty choice label', 'All'),
        widget=forms.Select)

    class Meta:
        model = User
        fields = []
