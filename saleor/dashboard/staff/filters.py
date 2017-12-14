from __future__ import unicode_literals

from django import forms
from django.contrib.auth.models import Group
from django.utils.translation import pgettext_lazy
from django_filters import (
    CharFilter, ChoiceFilter, ModelMultipleChoiceFilter, OrderingFilter)

from ...core.filters import SortedFilterSet
from ...userprofile.models import User
from ..customer.filters import UserFilter


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


class StaffFilter(UserFilter):
    groups = ModelMultipleChoiceFilter(
        label=pgettext_lazy('Staff list filter label', 'Groups'),
        name='groups',
        queryset=Group.objects.all())
    sort_by = OrderingFilter(
        label=pgettext_lazy('Staff list filter label', 'Sort by'),
        fields=SORT_BY_FIELDS,
        field_labels=SORT_BY_FIELDS_LABELS)

    class Meta:
        model = User
        fields = []
