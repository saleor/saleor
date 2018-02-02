from django.utils.translation import npgettext, pgettext_lazy
from django_filters import CharFilter, OrderingFilter

from ...core.filters import SortedFilterSet
from ...product.models import Collection

SORT_BY_FIELDS = {
    'name': pgettext_lazy('Collection list sorting option', 'name')}


class CollectionFilter(SortedFilterSet):
    name = CharFilter(
        label=pgettext_lazy('Collection list name filter label', 'Name'),
        lookup_expr='icontains')
    sort_by = OrderingFilter(
        label=pgettext_lazy('Collection list sorting filter label', 'Sort by'),
        fields=SORT_BY_FIELDS.keys(),
        field_labels=SORT_BY_FIELDS)

    class Meta:
        model = Collection
        fields = []

    def get_summary_message(self):
        counter = self.qs.count()
        return npgettext(
            'Number of matching records in the dashboard collections list',
            'Found %(counter)d matching collection',
            'Found %(counter)d matching collections',
            number=counter) % {'counter': counter}
