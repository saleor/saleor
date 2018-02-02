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
        name='created', widget=DateRangeWidget, method='filter_by_date_range')
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

    def filter_by_date_range(self, queryset, name, value):
        q = Q()
        if value.start:
            q = Q(start_date__gte=value.start)
        if value.stop:
            if value.start:
                q |= Q(end_date__lte=value.stop)
            else:
                q = Q(end_date__lte=value.stop)
        return queryset.filter(q)

    def get_summary_message(self):
        counter = self.qs.count()
        return npgettext(
            'Number of matching records in the dashboard vouchers list',
            'Found %(counter)d matching voucher',
            'Found %(counter)d matching vouchers',
            number=counter) % {'counter': counter}
