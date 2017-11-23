from django_filters import (FilterSet, OrderingFilter)
from django.utils.translation import pgettext_lazy

from ...product.models import Category


SORT_BY_FIELDS = {'name': pgettext_lazy('Product list sorting option', 'name')}


class CategoryFilter(FilterSet):
    sort_by = OrderingFilter(
        label=pgettext_lazy('Product list sorting filter label', 'Sort by'),
        fields=SORT_BY_FIELDS.keys(),
        field_labels=SORT_BY_FIELDS)

    class Meta:
        model = Category
        fields = []
