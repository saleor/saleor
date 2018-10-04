import graphene
from graphene import relay

from ...menu import models
from ..core.types.common import CountableDjangoObjectType


class MenuItem(CountableDjangoObjectType):
    url = graphene.String(description='URL to the menu item.')

    class Meta:
        description = """Represents a single item of the related menu.
        Can store categories, collection or pages."""
        interfaces = [relay.Node]
        exclude_fields = ['sort_order', 'lft', 'rght', 'tree_id']
        filter_fields = {}
        model = models.MenuItem


class Menu(CountableDjangoObjectType):
    items = graphene.List(
        MenuItem, required=True,
        description='List of menu items of the menu')

    class Meta:
        description = """Represents a single menu - an object that is used
        to help navigate through the store."""
        interfaces = [relay.Node]
        exclude_fields = ['json_content']
        filter_fields = {}
        model = models.Menu

    def resolve_items(self, info, **kwargs):
        return self.items.filter(level=0).select_related(
            'category', 'collection', 'page').all()
