from graphene import relay

from ...menu import models
from ..core.types import CountableDjangoObjectType


class Menu(CountableDjangoObjectType):
    class Meta:
        description = """Represents a single menu - an object that is used
        to help navigate through the store."""
        interfaces = [relay.Node]
        filter_fields = ['id', 'name']
        model = models.Menu


class MenuItem(CountableDjangoObjectType):
    class Meta:
        description = """Represents a single item of the related menu.
        Can store categories, collection or pages."""
        interfaces = [relay.Node]
        exclude_fields = ['lft', 'rght', 'tree_id']
        filter_fields = ['id', 'name']
        model = models.MenuItem
