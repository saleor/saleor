from __future__ import unicode_literals

from django.utils.translation import pgettext_lazy
from django_filters import CharFilter, OrderingFilter

from ...core.filters import SortedFilterSet
from ...product.models import Category

SORT_BY_FIELDS = {
    'name': pgettext_lazy('Category list sorting option', 'name'),
    'description': pgettext_lazy(
        'Category list sorting option', 'description'),
    'is_hidden': pgettext_lazy('Category list sorting option', 'is hidden')}

IS_HIDDEN_CHOICES = (
    ('1', pgettext_lazy('Is hidden filter choice', 'Hidden')),
    ('0', pgettext_lazy('Is hidden filter choice', 'Not hidden')))


class CategoryFilter(SortedFilterSet):
    name = CharFilter(
        label=pgettext_lazy('Category list filter label', 'Name'),
        lookup_expr='icontains')
    sort_by = OrderingFilter(
        label=pgettext_lazy('Category list sorting filter label', 'Sort by'),
        fields=SORT_BY_FIELDS.keys(),
        field_labels=SORT_BY_FIELDS)

    class Meta:
        model = Category
        fields = []
