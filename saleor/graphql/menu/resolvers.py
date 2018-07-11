from ...menu import models
from ..utils import filter_by_query_param

MENU_SEARCH_FIELDS = ('name',)
MENU_ITEM_SEARCH_FIELDS = ('name',)


def resolve_menus(info, query):
    queryset = models.Menu.objects.all()
    queryset = filter_by_query_param(queryset, query, MENU_SEARCH_FIELDS)
    return queryset


def resolve_menu_items(info, query):
    queryset = models.MenuItem.objects.all()
    queryset = filter_by_query_param(queryset, query, MENU_ITEM_SEARCH_FIELDS)
    return queryset
