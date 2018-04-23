from graphene import relay

from ...page import models
from ..core.types import CountableDjangoObjectType


class Page(CountableDjangoObjectType):
    class Meta:
        description = """A static page that can be manually added by a shop
        operator through the dashboard."""
        interfaces = [relay.Node]
        filter_fields = ['id', 'name']
        model = models.Page
