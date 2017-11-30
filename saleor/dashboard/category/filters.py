from __future__ import unicode_literals

from django_filters import OrderingFilter
from django.utils.translation import pgettext_lazy

from ...product.models import Category
from ..filters import SortedFilterSet


SORT_BY_FIELDS = {
    'name': pgettext_lazy('Category list sorting option', 'name'),
    'description': pgettext_lazy(
        'Category list sorting option', 'description')}


class CategoryFilter(SortedFilterSet):
    sort_by = OrderingFilter(
        label=pgettext_lazy('Product list sorting filter label', 'Sort by'),
        fields=SORT_BY_FIELDS.keys(),
        field_labels=SORT_BY_FIELDS)

    class Meta:
        model = Category
        fields = []
