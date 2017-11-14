from __future__ import unicode_literals

from django_filters import (FilterSet, RangeFilter, OrderingFilter)
from django.utils.translation import pgettext_lazy
from django_prices.models import PriceField

from ...discount.models import Sale, Voucher


SORT_BY_FIELDS_SALE = {
    'name': pgettext_lazy('Sale list sorting option', 'name'),
    'value': pgettext_lazy('Sale list sorting option', 'value')}

SORT_BY_FIELDS_VOUCHER = {
    'name': pgettext_lazy('Voucher list sorting option', 'name'),
    'discount_value': pgettext_lazy(
        'Voucher list sorting option', 'discount_value'),
    'apply_to': pgettext_lazy('Voucher list sorting option', 'apply_to'),
    'start_date': pgettext_lazy('Voucher list sorting option', 'start_date'),
    'end_date': pgettext_lazy('Voucher list sorting option', 'end_date'),
    'used': pgettext_lazy('Voucher list sorting option', 'used'),
    'limit': pgettext_lazy('Voucher list sorting option', 'limit')}


class SaleFilter(FilterSet):
    sort_by = OrderingFilter(
        label=pgettext_lazy('Sale list sorting form', 'Sort by'),
        fields=SORT_BY_FIELDS_SALE.keys(),
        field_labels=SORT_BY_FIELDS_SALE
    )

    class Meta:
        model = Sale
        fields = ['categories', 'type', 'value']


class VoucherFilter(FilterSet):
    sort_by = OrderingFilter(
        label=pgettext_lazy('Voucher list sorting form', 'Sort by'),
        fields=SORT_BY_FIELDS_VOUCHER.keys(),
        field_labels=SORT_BY_FIELDS_VOUCHER
    )

    class Meta:
        model = Voucher
        fields = ['name', 'discount_value_type', 'discount_value', 'apply_to',
                  'start_date', 'end_date', 'used', 'limit']
