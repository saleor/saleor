import graphene

from ...menu import models
from ..utils.filters import filter_by_query_param
from .types import Menu

MENU_SEARCH_FIELDS = ("name",)
MENU_ITEM_SEARCH_FIELDS = ("name",)


def resolve_menu(info, menu_id=None, name=None):
    assert menu_id or name, "No ID or name provided."
    if name is not None:
        return models.Menu.objects.filter(name=name).first()
    return graphene.Node.get_node_from_global_id(info, menu_id, Menu)


def resolve_menus(info, query, **_kwargs):
    qs = models.Menu.objects.all()
    return filter_by_query_param(qs, query, MENU_SEARCH_FIELDS)


def resolve_menu_items(info, query, **_kwargs):
    qs = models.MenuItem.objects.all()
    return filter_by_query_param(qs, query, MENU_ITEM_SEARCH_FIELDS)
