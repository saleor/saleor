import graphene
from graphql.error import GraphQLError

from ...menu import models
from ..utils.filters import filter_by_query_param
from .types import Menu
from ..core.validators import validate_query_args

MENU_SEARCH_FIELDS = ("name",)
MENU_ITEM_SEARCH_FIELDS = ("name",)


def resolve_menu(info, menu_id=None, name=None):
    validate_query_args(id=menu_id, name=name)
    if menu_id:
        return graphene.Node.get_node_from_global_id(info, menu_id, Menu)
    if name:
        return models.Menu.objects.filter(name=name).first()
    raise GraphQLError("Either 'id' or 'slug' argument is required")


def resolve_menus(info, query, **_kwargs):
    qs = models.Menu.objects.all()
    return filter_by_query_param(qs, query, MENU_SEARCH_FIELDS)


def resolve_menu_items(info, query, **_kwargs):
    qs = models.MenuItem.objects.all()
    return filter_by_query_param(qs, query, MENU_ITEM_SEARCH_FIELDS)
