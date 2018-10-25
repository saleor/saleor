import graphene
import graphene_django_optimizer as gql_optimizer
from django.db.models import Prefetch
from graphene import relay

from ...menu import models
from ..core.types.common import CountableDjangoObjectType


def prefetch_menus(info, *args, **kwargs):
    qs = models.MenuItem.objects.filter(level=0)
    return Prefetch(
        'items', queryset=gql_optimizer.query(qs, info),
        to_attr='prefetched_items')


class Menu(CountableDjangoObjectType):
    children = graphene.List(
        lambda: MenuItem, required=True,
        description='List of menu item children items')
    items = gql_optimizer.field(
        graphene.List(lambda: MenuItem),
        prefetch_related=prefetch_menus)

    class Meta:
        description = """Represents a single menu - an object that is used
        to help navigate through the store."""
        interfaces = [relay.Node]
        exclude_fields = ['json_content']
        model = models.Menu

    def resolve_items(self, info, **kwargs):
        if hasattr(self, 'prefetched_items'):
            return self.prefetched_items
        return self.items.filter(level=0)


class MenuItem(CountableDjangoObjectType):
    children = gql_optimizer.field(
        graphene.List(lambda: MenuItem), model_field='children')
    url = graphene.String(description='URL to the menu item.')

    class Meta:
        description = """Represents a single item of the related menu.
        Can store categories, collection or pages."""
        interfaces = [relay.Node]
        exclude_fields = ['sort_order', 'lft', 'rght', 'tree_id']
        model = models.MenuItem

    def resolve_children(self, info, **kwargs):
        return self.children.all()
