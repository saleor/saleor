import graphene
from graphene import relay

from ...menu import models
from ..core.types import CountableDjangoObjectType


class Menu(CountableDjangoObjectType):
    class Meta:
        description = """Represents a single menu - an object that is used
        to help navigate through the store."""
        interfaces = [relay.Node]
        filter_fields = {}
        model = models.Menu


class MenuItem(CountableDjangoObjectType):
    url = graphene.String(description='URL to the menu item.')

    class Meta:
        description = """Represents a single item of the related menu.
        Can store categories, collection or pages."""
        interfaces = [relay.Node]
        only_fields = ['children', 'id', 'menu', 'name', 'url']
        filter_fields = {}
        model = models.MenuItem

    def resolve_url(self, info):
        return self.get_url()
