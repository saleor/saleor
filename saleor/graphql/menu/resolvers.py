from ...menu import models
from ..utils import filter_by_query_param

MENU_SEARCH_FIELDS = ('name',)
MENU_ITEM_SEARCH_FIELDS = ('name',)


def resolve_menus(info, query):
    queryset = models.Menu.objects.all()
    return filter_by_query_param(queryset, query, MENU_SEARCH_FIELDS)


def resolve_menu_items(info, query):
    queryset = models.MenuItem.objects.all()
    return filter_by_query_param(queryset, query, MENU_ITEM_SEARCH_FIELDS)
