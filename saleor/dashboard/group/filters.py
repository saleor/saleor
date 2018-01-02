from django.contrib.auth.models import Group
from django.utils.translation import npgettext, pgettext_lazy
from django_filters import (
    CharFilter, ModelMultipleChoiceFilter, OrderingFilter)

from ...core.filters import SortedFilterSet
from ...core.permissions import get_permissions

SORT_BY_FIELDS = {
    'name': pgettext_lazy('Group list sorting option', 'name')}


class GroupFilter(SortedFilterSet):
    name = CharFilter(
        label=pgettext_lazy('Group list filter label', 'Name'),
        lookup_expr='icontains')
    permissions = ModelMultipleChoiceFilter(
        label=pgettext_lazy('Group list filter label', 'Permissions'),
        name='permissions',
        queryset=get_permissions())
    sort_by = OrderingFilter(
        label=pgettext_lazy('Group list filter label', 'Sort by'),
        fields=SORT_BY_FIELDS.keys(),
        field_labels=SORT_BY_FIELDS)

    class Meta:
        model = Group
        fields = []

    def get_summary_message(self):
        counter = self.qs.count()
        return npgettext(
            'Number of matching records in the dashboard groups list',
            'Found %(counter)d matching group',
            'Found %(counter)d matching groups',
            number=counter) % {'counter': counter}
