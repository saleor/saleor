from django import forms
from django.db.models import Q
from django.utils.translation import npgettext, pgettext_lazy
from django_countries import countries
from django_filters import CharFilter, ChoiceFilter, OrderingFilter

from ...account.models import Organization
from ...core.filters import SortedFilterSet

SORT_BY_FIELDS = (
    ('name', 'name'),
    ('default_billing_address__city', 'location'))

SORT_BY_FIELDS_LABELS = {
    'name': pgettext_lazy(
        'Organization list sorting option', 'name'),
    'default_billing_address__city': pgettext_lazy(
        'Organization list sorting option', 'location')}

IS_ACTIVE_CHOICES = (
    ('1', pgettext_lazy('Is active filter choice', 'Active')),
    ('0', pgettext_lazy('Is active filter choice', 'Not active')))


class OrganizationFilter(SortedFilterSet):
    name_or_email = CharFilter(
        label=pgettext_lazy('Organization and contacts name or email filter',
                            'Name or email'),
        method='filter_by_name_or_email')
    location = CharFilter(
        label=pgettext_lazy('Organization list filter label', 'Location'),
        method='filter_by_location')
    is_active = ChoiceFilter(
        label=pgettext_lazy('Organization list filter label', 'Is active'),
        choices=IS_ACTIVE_CHOICES,
        empty_label=pgettext_lazy('Filter empty choice label', 'All'),
        widget=forms.Select)
    sort_by = OrderingFilter(
        label=pgettext_lazy('Organization list filter label', 'Sort by'),
        fields=SORT_BY_FIELDS,
        field_labels=SORT_BY_FIELDS_LABELS)

    class Meta:
        model = Organization
        fields = []

    def filter_by_name_or_email(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value) |
            Q(contacts__user__email__icontains=value) |
            Q(contacts__user__first_name__icontains=value) |
            Q(contacts__user__last_name__icontains=value))

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
            'Number of matching records in the dashboard organizations list',
            'Found %(counter)d matching organization',
            'Found %(counter)d matching organizations',
            number=counter) % {'counter': counter}
