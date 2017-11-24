from __future__ import unicode_literals

from django.contrib.auth.models import Group
from django_filters import FilterSet, OrderingFilter
from django.utils.translation import pgettext_lazy


SORT_BY_FIELDS = {'name': pgettext_lazy('Group list sorting option', 'name')}


class GroupFilter(FilterSet):
    sort_by = OrderingFilter(
        label=pgettext_lazy('Product list sorting filter label', 'Sort by'),
        fields=SORT_BY_FIELDS.keys(),
        field_labels=SORT_BY_FIELDS)

    class Meta:
        model = Group
        fields = []
