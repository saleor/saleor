from __future__ import unicode_literals

from django_filters import (CharFilter, FilterSet, OrderingFilter)
from django_countries import countries
from django.db.models import Q
from django.utils.translation import pgettext_lazy

from ...userprofile.models import User


SORT_BY_FIELDS = (
    ('email', 'email'),
    ('default_billing_address__first_name', 'name'),
    ('default_billing_address__city', 'location')
)


SORT_BY_FIELDS_LABELS = {
    'email': pgettext_lazy(
        'Customer list sorting option', 'email'),
    'default_billing_address__first_name': pgettext_lazy(
        'Customer list sorting option', 'name'),
    'default_billing_address__city': pgettext_lazy(
        'Customer list sorting option', 'location')}


class StaffFilter(FilterSet):
    sort_by = OrderingFilter(
        label=pgettext_lazy('Staff list sorting filter', 'Sort by'),
        fields=SORT_BY_FIELDS,
        field_labels=SORT_BY_FIELDS_LABELS)
    name_or_email = CharFilter(
        label=pgettext_lazy('Customer name or email filter', 'Name or email'),
        method='filter_by_customer')
    location = CharFilter(
        label=pgettext_lazy('Customer list sorting filter', 'Location'),
        method='filter_by_location')

    class Meta:
        model = User
        fields = ['email', 'is_active', 'groups']

    def filter_by_customer(self, queryset, name, value):
        return queryset.filter(
            Q(email__icontains=value) |
            Q(default_billing_address__first_name__icontains=value) |
            Q(default_billing_address__last_name__icontains=value))

    def filter_by_location(self, queryset, name, value):
        for code, country in dict(countries).items():
            if value.lower() in country.lower():
                value = code
        return queryset.filter(
            Q(default_billing_address__city__icontains=value) |
            Q(default_billing_address__country__icontains=value))
