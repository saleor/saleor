from __future__ import unicode_literals

from django_filters import (
    CharFilter, ChoiceFilter, DateFromToRangeFilter, ModelMultipleChoiceFilter,
    OrderingFilter, RangeFilter)
from django.utils.translation import pgettext_lazy
from django import forms

from ...core.utils.filters import filter_by_date_range
from ...discount.models import Sale, Voucher
from ...product.models import Category
from ..filters import SortedFilterSet
from ..widgets import DateRangeWidget


SORT_BY_FIELDS_SALE = {
    'name': pgettext_lazy('Sale list sorting option', 'name'),
    'value': pgettext_lazy('Sale list sorting option', 'value')}

SORT_BY_FIELDS_LABELS_VOUCHER = {
    'name': pgettext_lazy('Voucher list sorting option', 'name'),
    'discount_value': pgettext_lazy(
        'Voucher list sorting option', 'discount_value'),
    'apply_to': pgettext_lazy('Voucher list sorting option', 'apply_to'),
    'start_date': pgettext_lazy('Voucher list sorting option', 'start_date'),
    'end_date': pgettext_lazy('Voucher list sorting option', 'end_date'),
    'used': pgettext_lazy('Voucher list sorting option', 'used'),
    'limit': pgettext_lazy('Voucher list sorting option', 'limit')}

DISCOUNT_TYPE_CHOICES = (
    ('fixed', pgettext_lazy('Sale type filter choice', 'USD')),
    ('percentage', pgettext_lazy('Sale type filter choice', '%')))


class SaleFilter(SortedFilterSet):
    name = CharFilter(
        label=pgettext_lazy('Sale list filter label', 'Name'),
        lookup_expr='icontains')
    categories = ModelMultipleChoiceFilter(
        label=pgettext_lazy('Sale list filter label', 'Categories'),
        name='categories',
        queryset=Category.objects.all())
    type = ChoiceFilter(
        label=pgettext_lazy('Sale list filter label', 'Discount type'),
        choices=DISCOUNT_TYPE_CHOICES,
        empty_label=pgettext_lazy('Filter empty choice label', 'All'),
        widget=forms.Select)
    value = RangeFilter(
        label=pgettext_lazy('Sale list filter label', 'Value'))
    sort_by = OrderingFilter(
        label=pgettext_lazy('Sale list filter label', 'Sort by'),
        fields=SORT_BY_FIELDS_SALE.keys(),
        field_labels=SORT_BY_FIELDS_SALE)

    class Meta:
        model = Sale
        fields = []


class VoucherFilter(SortedFilterSet):
    name = CharFilter(
        label=pgettext_lazy('Voucher list name filter label', 'Name'),
        lookup_expr='icontains')
    type = ChoiceFilter(
        name='discount_value_type',
        label=pgettext_lazy(
            'Sale list is sale type filter label', 'Discount type'),
        choices=DISCOUNT_TYPE_CHOICES,
        empty_label=pgettext_lazy('Filter empty choice label', 'All'),
        widget=forms.Select)
    discount_value = RangeFilter(
        label=pgettext_lazy('Sale list filter label', 'Discount_value'))
    date = DateFromToRangeFilter(
        label=pgettext_lazy(
            'Order list sorting filter label', 'Period of validity'),
        name='created', widget=DateRangeWidget, method=filter_by_date_range)
    limit = RangeFilter(
        label=pgettext_lazy('Voucher list sorting filter', 'Limit'),
        name='limit')
    sort_by = OrderingFilter(
        label=pgettext_lazy('Voucher list sorting filter label', 'Sort by'),
        fields=SORT_BY_FIELDS_LABELS_VOUCHER.keys(),
        field_labels=SORT_BY_FIELDS_LABELS_VOUCHER)

    class Meta:
        model = Voucher
        fields = []
