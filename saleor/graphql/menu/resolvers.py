import graphene
import graphene_django_optimizer as gql_optimizer

from ...menu import models
from ..utils import filter_by_query_param
from .types import Menu

MENU_SEARCH_FIELDS = ('name',)
MENU_ITEM_SEARCH_FIELDS = ('name',)


def resolve_menu(info, menu_id=None, name=None):
    assert menu_id or name, 'No ID or name provided.'
    if name is not None:
        qs = models.Menu.objects.filter(name=name)
        qs = gql_optimizer.query(qs, info)
        return qs[0] if qs else None
    return graphene.Node.get_node_from_global_id(info, menu_id, Menu)


def resolve_menus(info, query):
    qs = models.Menu.objects.all()
    qs = filter_by_query_param(qs, query, MENU_SEARCH_FIELDS)
    return gql_optimizer.query(qs, info)


def resolve_menu_items(info, query):
    qs = models.MenuItem.objects.all()
    qs = filter_by_query_param(qs, query, MENU_ITEM_SEARCH_FIELDS)
    return gql_optimizer.query(qs, info)
