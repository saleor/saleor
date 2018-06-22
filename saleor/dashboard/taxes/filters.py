from django import forms
from django.utils.translation import npgettext, pgettext_lazy
from django_filters import ChoiceFilter, OrderingFilter
from django_prices_vatlayer.models import VAT

from ...core.filters import SortedFilterSet
from ...core.utils import get_country_name_by_code

SORT_BY_FIELDS = {
    'country_code': pgettext_lazy(
        'Product list sorting option', 'country_code')}


def get_country_choices_for_vat():
    qs = VAT.objects.order_by('country_code')
    return [
        (country_code, get_country_name_by_code(country_code))
        for country_code in qs.values_list('country_code', flat=True)]


class TaxFilter(SortedFilterSet):
    country_code = ChoiceFilter(
        label=pgettext_lazy(
            'Taxes list filter label', 'Country name'),
        empty_label=pgettext_lazy('Filter empty choice label', 'All'),
        widget=forms.Select)
    sort_by = OrderingFilter(
        label=pgettext_lazy('Taxes list sorting form', 'Sort by'),
        fields=SORT_BY_FIELDS.keys(),
        field_labels=SORT_BY_FIELDS)

    class Meta:
        model = VAT
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filters['country_code'].extra.update({
            'choices': get_country_choices_for_vat()})

    def get_summary_message(self):
        counter = self.qs.count()
        return npgettext(
            'Number of matching records in the dashboard taxes list',
            'Found %(counter)d matching country',
            'Found %(counter)d matching countries',
            number=counter) % {'counter': counter}
