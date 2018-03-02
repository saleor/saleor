from django.utils.translation import npgettext, pgettext_lazy
from django_filters import CharFilter, OrderingFilter

from ...menu.models import Menu
from ...core.filters import SortedFilterSet

SORT_BY_FIELDS = {
    'slug': pgettext_lazy('Menu list sorting option', 'Internal name')}


class MenuFilter(SortedFilterSet):
    slug = CharFilter(
        label=pgettext_lazy('Menu list filter label', 'Internal name'),
        lookup_expr='icontains')
    sort_by = OrderingFilter(
        label=pgettext_lazy('Menu list filter label', 'Sort by'),
        fields=SORT_BY_FIELDS.keys(),
        field_labels=SORT_BY_FIELDS)

    class Meta:
        model = Menu
        fields = []

    def get_summary_message(self):
        counter = self.qs.count()
        return npgettext(
            'Number of matching records in the dashboard menus list',
            'Found %(counter)d matching menu',
            'Found %(counter)d matching menus',
            number=counter) % {'counter': counter}
