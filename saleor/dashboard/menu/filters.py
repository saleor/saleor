from django.utils.translation import npgettext, pgettext_lazy
from django_filters import CharFilter, NumberFilter, OrderingFilter

from ...menu.models import Menu, MenuItem
from ...core.filters import SortedFilterSet

MENU_SORT_BY_FIELDS = {
    'slug': pgettext_lazy('Menu list sorting option', 'Internal name')}

MENU_ITEM_SORT_BY_FIELDS = {
    'name': pgettext_lazy('Menu item list sorting option', 'Name'),
    'sort_order': pgettext_lazy('Menu item list sorting option', 'sort_order'),
    'url': pgettext_lazy('Menu item list sorting option', 'URL')}


class MenuFilter(SortedFilterSet):
    slug = CharFilter(
        label=pgettext_lazy('Menu list filter label', 'Internal name'),
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
    sort_order = NumberFilter(
        label=pgettext_lazy('Menu item list filter label', 'Sorting order'))
    url = CharFilter(
        label=pgettext_lazy('Menu item list filter label', 'URL'),
        lookup_expr='icontains')
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
