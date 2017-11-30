from __future__ import unicode_literals

from django_filters import (
    CharFilter, ChoiceFilter, ModelMultipleChoiceFilter, OrderingFilter)
from django.contrib.auth.models import Group
from django.utils.translation import pgettext_lazy
from django import forms

from ...core.utils.filters import filter_by_customer, filter_by_location
from ...userprofile.models import User
from ..filters import SortedFilterSet


SORT_BY_FIELDS = (
    ('email', 'email'),
    ('default_billing_address__first_name', 'name'),
    ('default_billing_address__city', 'location'))

SORT_BY_FIELDS_LABELS = {
    'email': pgettext_lazy(
        'Customer list sorting option', 'email'),
    'default_billing_address__first_name': pgettext_lazy(
        'Customer list sorting option', 'name'),
    'default_billing_address__city': pgettext_lazy(
        'Customer list sorting option', 'location')}

IS_ACTIVE_CHOICES = (
    ('1', pgettext_lazy('Is active filter choice', 'Active')),
    ('0', pgettext_lazy('Is active filter choice', 'Not active')))


class StaffFilter(SortedFilterSet):
    name_or_email = CharFilter(
        label=pgettext_lazy('Staff list filter label', 'Name or email'),
        method=filter_by_customer)
    location = CharFilter(
        label=pgettext_lazy('Staff list filter label', 'Location'),
        method=filter_by_location)
    groups = ModelMultipleChoiceFilter(
        label=pgettext_lazy('Staff list filter label', 'Groups'),
        name='groups',
        queryset=Group.objects.all())
    is_active = ChoiceFilter(
        label=pgettext_lazy('Staff list filter label', 'Is active'),
        choices=IS_ACTIVE_CHOICES,
        empty_label=pgettext_lazy('Filter empty choice label', 'All'),
        widget=forms.Select)
    sort_by = OrderingFilter(
        label=pgettext_lazy('Staff list filter label', 'Sort by'),
        fields=SORT_BY_FIELDS,
        field_labels=SORT_BY_FIELDS_LABELS)

    class Meta:
        model = User
        fields = []
