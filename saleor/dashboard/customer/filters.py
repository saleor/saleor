from django import forms
from django.db.models import Q
from django.utils.translation import npgettext, pgettext_lazy
from django_countries import countries
from django_filters import CharFilter, ChoiceFilter, OrderingFilter

from ...account.models import User
from ...core.filters import SortedFilterSet

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


class UserFilter(SortedFilterSet):
    name_or_email = CharFilter(
        label=pgettext_lazy('Customer name or email filter', 'Name or email'),
        method='filter_by_customer')
    location = CharFilter(
        label=pgettext_lazy('Customer list filter label', 'Location'),
        method='filter_by_location')
    is_active = ChoiceFilter(
        label=pgettext_lazy('Customer list filter label', 'Is active'),
        choices=IS_ACTIVE_CHOICES,
        empty_label=pgettext_lazy('Filter empty choice label', 'All'),
        widget=forms.Select)
    sort_by = OrderingFilter(
        label=pgettext_lazy('Customer list filter label', 'Sort by'),
        fields=SORT_BY_FIELDS,
        field_labels=SORT_BY_FIELDS_LABELS)

    class Meta:
        model = User
        fields = []

    def filter_by_customer(self, queryset, name, value):
        return queryset.filter(
            Q(email__icontains=value) |
            Q(default_billing_address__first_name__icontains=value) |
            Q(default_billing_address__last_name__icontains=value))

    def filter_by_location(self, queryset, name, value):
        q = Q(default_billing_address__city__icontains=value)
        q |= Q(default_billing_address__country__icontains=value)
        country_codes = self.get_mapped_country_codes_from_search(value)
        for code in country_codes:
            q |= Q(default_billing_address__country__icontains=code)
        return queryset.filter(q)

    def get_mapped_country_codes_from_search(self, value):
        country_codes = []
        for code, country in dict(countries).items():
            if value.lower() in country.lower():
                country_codes.append(code)
        return country_codes

    def get_summary_message(self):
        counter = self.qs.count()
        return npgettext(
            'Number of matching records in the dashboard customers list',
            'Found %(counter)d matching customer',
            'Found %(counter)d matching customers',
            number=counter) % {'counter': counter}
