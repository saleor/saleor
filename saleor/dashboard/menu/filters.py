from django.db.models import Q
from django.utils.translation import npgettext, pgettext_lazy
from django_filters import CharFilter, OrderingFilter

from ...core.filters import SortedFilterSet
from ...menu.models import Menu, MenuItem

MENU_SORT_BY_FIELDS = {
    'name': pgettext_lazy('Menu list sorting option', 'Name')}

MENU_ITEM_SORT_BY_FIELDS = {
    'name': pgettext_lazy('Menu item list sorting option', 'Name')}


class MenuFilter(SortedFilterSet):
    name = CharFilter(
        label=pgettext_lazy('Menu list filter label', 'Menu name'),
        lookup_expr='icontains')
    sort_by = OrderingFilter(
        label=pgettext_lazy('Menu list filter label', 'Sort by'),
        fields=MENU_SORT_BY_FIELDS.keys(),
        field_labels=MENU_SORT_BY_FIELDS)

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


class MenuItemFilter(SortedFilterSet):
    name = CharFilter(
        label=pgettext_lazy('Menu item list filter label', 'Name'),
        lookup_expr='icontains')
    link = CharFilter(
        label=pgettext_lazy('Menu item list filter label', 'Points to'),
        method='filter_by_link')
    sort_by = OrderingFilter(
        label=pgettext_lazy('Menu item list sorting filter label', 'Sort by'),
        fields=MENU_ITEM_SORT_BY_FIELDS.keys(),
        field_labels=MENU_ITEM_SORT_BY_FIELDS)

    class Meta:
        model = MenuItem
        fields = []

    def get_summary_message(self):
        counter = self.qs.count()
        return npgettext(
            'Number of matching records in the dashboard menu items list',
            'Found %(counter)d matching menu item',
            'Found %(counter)d matching menu items',
            number=counter) % {'counter': counter}

    def filter_by_link(self, queryset, name, value):
        return queryset.filter(
            Q(collection__name__icontains=value) |
            Q(category__name__icontains=value) |
            Q(page__title__icontains=value) |
            Q(url__icontains=value))
