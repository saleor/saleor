from django.utils.translation import npgettext, pgettext_lazy
from django_filters import CharFilter, OrderingFilter

from ...core.filters import SortedFilterSet
from ...page.models import Page

SORT_BY_FIELDS = {
    'title': pgettext_lazy('Page list sorting option', 'title'),
    'url': pgettext_lazy('Page list sorting option', 'url')}


class PageFilter(SortedFilterSet):
    title = CharFilter(
        label=pgettext_lazy('Page list title filter label', 'Title'),
        lookup_expr='icontains')
    url = CharFilter(
        label=pgettext_lazy('Page list url filter label', 'URL'),
        lookup_expr='icontains')
    sort_by = OrderingFilter(
        label=pgettext_lazy('Page list sorting filter label', 'Sort by'),
        fields=SORT_BY_FIELDS.keys(),
        field_labels=SORT_BY_FIELDS)

    class Meta:
        model = Page
        fields = []

    def get_summary_message(self):
        counter = self.qs.count()
        return npgettext(
            'Number of matching records in the dashboard page list',
            'Found %(counter)d matching page',
            'Found %(counter)d matching pages',
            number=counter) % {'counter': counter}
