from graphene import relay

from ...page import models
from ..core.types import CountableDjangoObjectType


class Page(CountableDjangoObjectType):
    class Meta:
        description = """A static page that can be manually added by a shop
        operator through the dashboard."""
        interfaces = [relay.Node]
        model = models.Page
        filter_fields = ['id', 'name']


def resolve_pages(user):
    if user.is_authenticated and user.is_active and user.is_staff:
        return models.Page.objects.all().distinct()
    return models.Page.objects.public().distinct()
