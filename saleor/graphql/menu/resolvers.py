from ...menu import models
from ..utils import filter_by_query_param

MENU_SEARCH_FIELDS = ATTRIBUTES_SEARCH_FIELDS = ('name')

def resolve_menus(info):
    return models.Menu.objects.all()


def resolve_menu_items(info, query):
    queryset = models.MenuItem.objects.all()
    queryset = filter_by_query_param(queryset, query, ATTRIBUTES_SEARCH_FIELDS)
    return queryset
