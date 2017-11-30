from __future__ import unicode_literals

from django.contrib.auth.models import Group
from django_filters import (
    CharFilter, ModelMultipleChoiceFilter, OrderingFilter)
from django.utils.translation import pgettext_lazy

from ...core.permissions import get_permissions
from ..filters import SortedFilterSet


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
