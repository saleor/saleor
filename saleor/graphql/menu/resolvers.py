import graphene

from ...menu import models
from ..utils import filter_by_query_param
from .types import Menu

MENU_SEARCH_FIELDS = ('name',)
MENU_ITEM_SEARCH_FIELDS = ('name',)


def resolve_menu(info, id=None, name=None):
    assert id or name, 'No ID or name provided.'
    if name is not None:
        try:
            return models.Menu.objects.get(name=name)
        except models.Menu.DoesNotExist:
            return None
    return graphene.Node.get_node_from_global_id(info, id, Menu)


def resolve_menus(info, query):
    queryset = models.Menu.objects.all()
    return filter_by_query_param(queryset, query, MENU_SEARCH_FIELDS)


def resolve_menu_items(info, query):
    queryset = models.MenuItem.objects.all()
    return filter_by_query_param(queryset, query, MENU_ITEM_SEARCH_FIELDS)
