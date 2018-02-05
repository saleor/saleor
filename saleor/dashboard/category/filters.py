from django.utils.translation import npgettext, pgettext_lazy
from django_filters import CharFilter, OrderingFilter

from ...core.filters import SortedFilterSet
from ...product.models import Category

SORT_BY_FIELDS = {
    'name': pgettext_lazy('Category list sorting option', 'name'),
    'description': pgettext_lazy(
        'Category list sorting option', 'description')}


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

    def get_summary_message(self):
        counter = self.qs.count()
        return npgettext(
            'Number of matching records in the dashboard categories list',
            'Found %(counter)d matching category',
            'Found %(counter)d matching categories',
            number=counter) % {'counter': counter}
