from django import forms
from django.db.models import Q
from django.utils.translation import npgettext, pgettext_lazy
from django_filters import (
    CharFilter, ChoiceFilter, DateFromToRangeFilter, ModelMultipleChoiceFilter,
    OrderingFilter, RangeFilter)

from ...core.filters import SortedFilterSet
from ...discount.models import Sale, Voucher
from ...product.models import Category
from ..widgets import DateRangeWidget

SORT_BY_FIELDS_SALE = {
    'name': pgettext_lazy('Sale list sorting option', 'name'),
    'value': pgettext_lazy('Sale list sorting option', 'value'),
    'start_date': pgettext_lazy('Sale list sorting option', 'start_date'),
    'end_date': pgettext_lazy('Sale list sorting option', 'end_date')}

SORT_BY_FIELDS_LABELS_VOUCHER = {
    'name': pgettext_lazy('Voucher list sorting option', 'name'),
    'discount_value': pgettext_lazy(
        'Voucher list sorting option', 'discount_value'),
    'countries': pgettext_lazy('Voucher list sorting option', 'countries'),
    'start_date': pgettext_lazy('Voucher list sorting option', 'start_date'),
    'end_date': pgettext_lazy('Voucher list sorting option', 'end_date'),
    'used': pgettext_lazy('Voucher list sorting option', 'used'),
    'min_amount_spent': pgettext_lazy(
        'Voucher list sorting option', 'min_amount_spent')}

DISCOUNT_TYPE_CHOICES = (
    ('fixed', pgettext_lazy('Sale type filter choice', 'USD')),
    ('percentage', pgettext_lazy('Sale type filter choice', '%')))


def filter_by_date_range(queryset, name, value):
    q = Q()
    if value.start:
        q = Q(start_date__gte=value.start)
    if value.stop:
        if value.start:
            q |= Q(end_date__lte=value.stop)
        else:
            q = Q(end_date__lte=value.stop)
    return queryset.filter(q)


class SaleFilter(SortedFilterSet):
    name = CharFilter(
        label=pgettext_lazy('Sale list filter label', 'Name'),
        lookup_expr='icontains')
    categories = ModelMultipleChoiceFilter(
        label=pgettext_lazy('Sale list filter label', 'Categories'),
        field_name='categories',
        queryset=Category.objects.all())
    type = ChoiceFilter(
        label=pgettext_lazy('Sale list filter label', 'Discount type'),
        choices=DISCOUNT_TYPE_CHOICES,
        empty_label=pgettext_lazy('Filter empty choice label', 'All'),
        widget=forms.Select)
    value = RangeFilter(
        label=pgettext_lazy('Sale list filter label', 'Value'))
    date = DateFromToRangeFilter(
        label=pgettext_lazy(
            'Sale list sorting filter label', 'Period of validity'),
        field_name='created', widget=DateRangeWidget,
        method=filter_by_date_range)
    sort_by = OrderingFilter(
        label=pgettext_lazy('Sale list filter label', 'Sort by'),
        fields=SORT_BY_FIELDS_SALE.keys(),
        field_labels=SORT_BY_FIELDS_SALE)

    class Meta:
        model = Sale
        fields = []

    def get_summary_message(self):
        counter = self.qs.count()
        return npgettext(
            'Number of matching records in the dashboard sales list',
            'Found %(counter)d matching sale',
            'Found %(counter)d matching sales',
            number=counter) % {'counter': counter}


class VoucherFilter(SortedFilterSet):
    name = CharFilter(
        label=pgettext_lazy('Voucher list name filter label', 'Name'),
        lookup_expr='icontains')
    type = ChoiceFilter(
        field_name='discount_value_type',
        label=pgettext_lazy(
            'Sale list is sale type filter label', 'Discount type'),
        choices=DISCOUNT_TYPE_CHOICES,
        empty_label=pgettext_lazy('Filter empty choice label', 'All'),
        widget=forms.Select)
    discount_value = RangeFilter(
        label=pgettext_lazy('Sale list filter label', 'Discount_value'))
    date = DateFromToRangeFilter(
        label=pgettext_lazy(
            'Voucher list sorting filter label', 'Period of validity'),
        field_name='created', widget=DateRangeWidget,
        method=filter_by_date_range)
    min_amount_spent = RangeFilter(
        label=pgettext_lazy(
            'Voucher list sorting filter', 'Minimum amount spent'),
        field_name='min_amount_spent')
    sort_by = OrderingFilter(
        label=pgettext_lazy('Voucher list sorting filter label', 'Sort by'),
        fields=SORT_BY_FIELDS_LABELS_VOUCHER.keys(),
        field_labels=SORT_BY_FIELDS_LABELS_VOUCHER)

    class Meta:
        model = Voucher
        fields = []

    def get_summary_message(self):
        counter = self.qs.count()
        return npgettext(
            'Number of matching records in the dashboard vouchers list',
            'Found %(counter)d matching voucher',
            'Found %(counter)d matching vouchers',
            number=counter) % {'counter': counter}
